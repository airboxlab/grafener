import copy
import logging
from datetime import datetime

from attr import dataclass
from pandas import DataFrame

from grafener.logging_config import init_logging
from grafener.source import Source

init_logging()


@dataclass(frozen=True)
class TimeSeriesResponse:
    """Grafana timeseries response."""

    target: str
    datapoints: list[list[int | float]]

    def serialize(self):
        return {"target": self.target, "datapoints": self.datapoints}


@dataclass(frozen=True)
class TableResponse:
    """Grafana table response."""

    columns: list[dict[str, str]]
    rows: list[list[int | float | str]]
    type: str = "table"

    def serialize(self):
        return {"type": self.type, "columns": self.columns, "rows": self.rows}


def _to_time_series_response(target: str, df: DataFrame, experiment: str | None) -> TimeSeriesResponse:
    """Transforms given DataFrame in expected TimeSeries response format."""
    return TimeSeriesResponse(
        target=_prefix_target_xp(target, experiment),
        datapoints=list(
            zip(df[target].values.tolist(), [int(t.timestamp()) * 1000 for t in df.index.tolist()])
        ),  # noqa
    )


def _to_table_response(targets: list[str], df: DataFrame, experiment: str | None) -> TableResponse:
    """Transforms given DataFrame in expected Table response format."""
    return TableResponse(
        columns=[{"text": "Time", "type": "time"}]
        + [{"text": _prefix_target_xp(target, experiment), "type": "number"} for target in targets],
        rows=[
            [v[0], *v[1]]
            for v in list(zip([int(t.timestamp()) * 1000 for t in df.index.tolist()], df[targets].values.tolist()))
        ],
    )


def _fetch(source: Source, header_only: bool, use_cols: list[str] | None) -> DataFrame:
    """Calls appropriate fetcher, based on source type."""
    return source.read_source(header_only, use_cols)


def _prefix_target_xp(c: str, experiment: str | None) -> str:
    """If experiment is provided, add it as a prefix to given name."""
    return experiment + " -- " + c if experiment else c


def get_metrics(source: Source, search: str | None, experiment: str | None = None) -> list[str]:
    """Computes Grafana metrics from CSV header columns.

    :param source: a metrics source
    :param search: an optional search string passed in request
    :param experiment: an optional experiment ID passed as path parameter during datasource configuration. Used to
                       prefix metric names for deduplication when more than 1 datasource is used in a panel
    :return: list of queryable metrics
    """
    logging.info(f"metric search - xp: {experiment} source: {source} target: {search}")
    df = _fetch(source, header_only=True, use_cols=None)

    return [_prefix_target_xp(c, experiment) for c in df.columns if c != "Date/Time" and (search or "") in c]


def get_data(
    source: Source,
    targets: list[dict[str, str]],
    response_type: str,
    range_from: str,
    range_to: str,
    experiment: str | None = None,
) -> list[TimeSeriesResponse | TableResponse]:
    """Implements /query enpoint by querying source DataFrame and returning either a
    TimeSeriesResponse or a TableResponse.

    :param source: a data source
    :param targets: list of targets
    :param response_type: expected response type, either 'timeserie' or 'table'. Assuming same for all targets
    :param range_from: from date expressed in iso8601
    :param range_to: to date expressed in iso8601
    :param experiment: an optional experiment ID passed as path parameter during datasource configuration. When defined,
                       targets have it as a name prefix
    :return:
    """
    # remove experiment ID prefix from targets
    xp_free_targets = copy.deepcopy(targets)
    if experiment:
        for t in xp_free_targets:
            t["target"] = t["target"].replace(experiment + " -- ", "")

    # fetch data
    use_cols = list({t["target"] for t in xp_free_targets})
    # reintroduce extra space for last column, if it was requested
    available_cols = _fetch(source, header_only=True, use_cols=None)
    if available_cols.columns[-1] in use_cols:
        use_cols.append(available_cols.columns[-1] + " ")
        use_cols.remove(available_cols.columns[-1])
    df = _fetch(source, header_only=False, use_cols=use_cols)

    # filter data with specified time range
    range_from_dt = datetime.fromisoformat(range_from.replace("Z", "+00:00"))
    range_to_dt = datetime.fromisoformat(range_to.replace("Z", "+00:00"))
    df = df[(df.index >= range_from_dt) & (df.index <= range_to_dt)]

    # process each target and transform to requested response type
    if response_type == "timeserie":
        resp = [
            _to_time_series_response(target_definition["target"], df, experiment)
            for target_definition in xp_free_targets
        ]
    elif response_type == "table":
        resp = [_to_table_response([t["target"] for t in xp_free_targets], df, experiment)]
    else:
        raise ValueError(f"unsupported response type {response_type}")

    del df
    return resp
