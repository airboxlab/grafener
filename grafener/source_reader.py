import copy
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, NamedTuple, Optional, Union

import pandas as pd
from pandas import DataFrame

from grafener.logging_config import init_logging

init_logging()

# EnergyPlus date format doesn't include year by default
PINNED_SIM_YEAR: int = int(os.getenv("SIM_YEAR", datetime.now().year))
logging.info("Using pinned simulation year: {}".format(PINNED_SIM_YEAR))


# keep a cache for each source. Source data is invalidated if remote source changes
# (e.g. file timestamp changes in case)
class _DataFrameCacheValue(NamedTuple):
    timestamp: int
    data_frame: DataFrame


data_cache: Dict[str, _DataFrameCacheValue] = {}


# Response types
class TimeSeriesResponse:
    target: str
    datapoints: List[List[Union[int, float]]]

    def serialize(self):
        return {
            "target": self.target,
            "datapoints": self.datapoints
        }


class TableResponse:
    type: str = "table"
    columns: List[Dict[str, str]]
    rows: List[Union[int, float, str]]

    def serialize(self):
        return {
            "type": self.type,
            "columns": self.columns,
            "rows": self.rows
        }


def _to_time_series_response(target: str, df: DataFrame, experiment: Optional[str]) -> TimeSeriesResponse:
    resp = TimeSeriesResponse()
    resp.target = _prefix_target_xp(target, experiment)
    resp.datapoints = list(zip(df[target].values.tolist(),
                               [int(t.timestamp()) * 1000 for t in df.index.tolist()]))  # noqa
    return resp


def _to_table_response(targets: List[str], df: DataFrame, experiment: Optional[str]) -> TableResponse:
    resp = TableResponse()
    resp.columns = [{"text": "Time", "type": "time"}] + \
                   [{"text": _prefix_target_xp(target, experiment), "type": "number"} for target in targets]
    resp.rows = [[v[0], *v[1]]
                 for v in list(zip([int(t.timestamp()) * 1000 for t in df.index.tolist()],
                                   df[targets].values.tolist()))]
    return resp


def _local_file_reload_needed(source: str) -> bool:
    """

    :param source:
    :return: True if source can't be found in cache, or if associated timestamp is older than file modification time
    """
    return source not in data_cache or data_cache[source].timestamp < os.path.getmtime(source)


def _process_energyplus_datetime(strdate: str) -> str:
    """
    transforms:
        - EnergyPlus date format '%m/%d %H:%M:%S' to '%Y/%m/%d %H:%M:%S'.
        - midnight expressed as 24:00 into 00:00

    :param strdate:
    :return:
    """
    if "24:00" in strdate:
        date = strdate.strip().split(" ")[0]
        new_date = datetime.strptime(date, "%m/%d") + timedelta(days=1)
        return "{:04d}/{:02d}/{:02d}  00:00:00".format(PINNED_SIM_YEAR, new_date.month, new_date.day)
    else:
        return "{:04d}/{}".format(PINNED_SIM_YEAR, strdate.strip())


def _process_csv(df: DataFrame) -> DataFrame:
    """

    :param df:
    :return:
    """
    # make a nice datetime format out of Date/Time column
    df["Date/Time"] = df["Date/Time"].apply(_process_energyplus_datetime)
    df["Date/Time"] = pd.to_datetime(df["Date/Time"], format="%Y/%m/%d  %H:%M:%S", utc=True)
    df.index = df["Date/Time"]
    # last column has a trailing space
    df.columns = [c.strip() for c in df.columns]
    # drop NaNs: happens when source contains variables/meters reported at different frequency
    df = df.dropna()
    return df


def _fetch_local(source: str) -> DataFrame:
    """
    load data from local file system (uses cache)

    :param source:
    :return:
    """
    if _local_file_reload_needed(source):
        csv_data = _process_csv(pd.read_csv(source))
        data_cache[source] = _DataFrameCacheValue(int(datetime.now().timestamp()), csv_data)
    return data_cache[source].data_frame


def _fetch(source: str) -> DataFrame:
    """
    calls appropriate fetcher, based on source type. For now only local file systems is supported

    :param source:
    :return:
    """
    return _fetch_local(source)


def _prefix_target_xp(c: str, experiment: Optional[str]) -> str:
    """
    if experiment is provided, add it as a prefix to given name

    :param c:
    :param experiment:
    :return:
    """
    return experiment + " -- " + c if experiment else c


def get_metrics(source: str,
                search: Optional[str],
                experiment: Optional[str] = None) -> List[str]:
    """
    computes Grafana metrics from CSV header columns

    :param source:
    :param search: an optional search string passed in request
    :param experiment: an optional experiment ID passed as path parameter during datasource configuration. Used to
                       prefix metric names for deduplication when more than 1 datasource is used in a panel
    :return:
    """
    logging.info("metric search - xp: {} source: {} target: {}".format(experiment, source, search))
    df = _fetch(source)

    return [_prefix_target_xp(c, experiment)
            for c in df.columns if c != "Date/Time" and (search or "") in c]


def get_data(source: str,
             targets: List[Dict[str, str]],
             response_type: str,
             range_from: str,
             range_to: str,
             experiment: Optional[str] = None) -> List[Union[TimeSeriesResponse, TableResponse]]:
    """
    implements /query enpoint by querying source DataFrame and returning either a TimeSeriesResponse or a TableResponse

    :param source: source file
    :param targets: list of targets
    :param response_type: expected response type, either 'timeserie' or 'table'. Assuming same for all targets
    :param range_from: from date expressed in iso8601
    :param range_to: to date expressed in iso8601
    :param experiment: an optional experiment ID passed as path parameter during datasource configuration. When defined,
                       targets have it as a name prefix
    :return:
    """
    df = _fetch(source)

    # remove experiment ID prefix from targets
    xp_free_targets = copy.deepcopy(targets)
    if experiment:
        for t in xp_free_targets:
            t["target"] = t["target"].replace(experiment + " -- ", "")

    # filter data with specified time range
    range_from_dt = datetime.fromisoformat(range_from.replace("Z", "+00:00"))
    range_to_dt = datetime.fromisoformat(range_to.replace("Z", "+00:00"))
    df = df[(df.index >= range_from_dt) & (df.index <= range_to_dt)]

    # process each target and transform to requested response type
    if response_type == "timeserie":
        return [_to_time_series_response(target_definition["target"], df, experiment)
                for target_definition in xp_free_targets]
    elif response_type == "table":
        return [_to_table_response([t["target"] for t in xp_free_targets], df, experiment)]
    else:
        raise ValueError("unsupported response type {}".format(response_type))
