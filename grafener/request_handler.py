import copy
import logging
from datetime import datetime
from typing import Dict, List, Optional, Union

from pandas import DataFrame

from grafener.logging_config import init_logging
from grafener.source import Source
from grafener.types import DataFrameCacheValue, TimeSeriesResponse, TableResponse

init_logging()

# keep a cache for each source. Source data is invalidated if remote source changes
# (e.g. file timestamp changes in case)
data_cache: Dict[str, DataFrameCacheValue] = {}


def _to_time_series_response(target: str, df: DataFrame, experiment: Optional[str]) -> TimeSeriesResponse:
    """transforms given DataFrame in expected TimeSeries response format"""
    return TimeSeriesResponse(
        target=_prefix_target_xp(target, experiment),
        datapoints=list(zip(df[target].values.tolist(), [int(t.timestamp()) * 1000 for t in df.index.tolist()])) # noqa
    )


def _to_table_response(targets: List[str], df: DataFrame, experiment: Optional[str]) -> TableResponse:
    """transforms given DataFrame in expected Table response format"""
    return TableResponse(
        columns=[{"text": "Time", "type": "time"}] +
                [{"text": _prefix_target_xp(target, experiment), "type": "number"} for target in targets],
        rows=[[v[0], *v[1]]
              for v in list(zip([int(t.timestamp()) * 1000 for t in df.index.tolist()],
                                df[targets].values.tolist()))]
    )


def _fetch(source: str) -> DataFrame:
    """calls appropriate fetcher, based on source type"""
    src = Source.of(source)
    refresh_needed = source not in data_cache or data_cache[source].timestamp < src.source_timestamp()
    if refresh_needed:
        csv_data = src.read_source()
        data_cache[source] = DataFrameCacheValue(int(datetime.now().timestamp()), csv_data)
    return data_cache[source].data_frame


def _prefix_target_xp(c: str, experiment: Optional[str]) -> str:
    """if experiment is provided, add it as a prefix to given name"""
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
    :return: list of queryable metrics
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
