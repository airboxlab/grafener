from typing import NamedTuple, List, Union, Dict

from pandas import DataFrame


class DataFrameCacheValue(NamedTuple):
    """Tuple representing a DataFrame cache entry"""
    timestamp: int
    data_frame: DataFrame


class TimeSeriesResponse:
    """Grafana timeseries response"""
    target: str
    datapoints: List[List[Union[int, float]]]

    def serialize(self):
        return {
            "target": self.target,
            "datapoints": self.datapoints
        }


class TableResponse:
    """Grafana table response"""
    type: str = "table"
    columns: List[Dict[str, str]]
    rows: List[Union[int, float, str]]

    def serialize(self):
        return {
            "type": self.type,
            "columns": self.columns,
            "rows": self.rows
        }
