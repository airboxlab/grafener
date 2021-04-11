from typing import NamedTuple, List, Union, Dict

from attr import dataclass
from pandas import DataFrame


class DataFrameCacheValue(NamedTuple):
    """Tuple representing a DataFrame cache entry"""
    timestamp: int
    data_frame: DataFrame


@dataclass(frozen=True)
class TimeSeriesResponse:
    """Grafana timeseries response"""
    target: str
    datapoints: List[List[Union[int, float]]]

    def serialize(self):
        return {
            "target": self.target,
            "datapoints": self.datapoints
        }


@dataclass(frozen=True)
class TableResponse:
    """Grafana table response"""
    columns: List[Dict[str, str]]
    rows: List[List[Union[int, float, str]]]
    type: str = "table"

    def serialize(self):
        return {
            "type": self.type,
            "columns": self.columns,
            "rows": self.rows
        }
