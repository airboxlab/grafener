import logging
import os
import tempfile
from abc import ABC, abstractmethod
from urllib.parse import urlparse

import boto3
import pandas as pd
from pandas import DataFrame

from grafener.energyplus import process_csv

# make boto3 less verbose
for logger in ["boto3", "botocore", "s3transfer", "urllib3"]:
    logging.getLogger(logger).setLevel(logging.ERROR)


class Source(ABC):
    """An abstract source."""

    def __init__(self, source_path: str, sim_year: int):
        self.source_path = source_path
        self.sim_year = sim_year

    def read_source(self, header_only: bool, use_cols: list[str] | None) -> DataFrame:
        """Read source and apply necessary transformations.

        :param header_only: read only the header, useful to get column names
        :param use_cols: columns to read. Must be provided if header_only is False
        """

        if header_only:
            # read only the header
            cols_df = pd.read_csv(self.load(), nrows=0)
            cols_df.columns = [col.strip() for col in cols_df.columns]
            return cols_df
        else:
            assert use_cols, "use_cols must be provided"
            # make sure Date/Time is always present, as it's used as index
            if "Date/Time" not in use_cols:
                use_cols.append("Date/Time")
            # read and process the whole file
            return process_csv(pd.read_csv(self.load(), usecols=use_cols), sim_year=self.sim_year)

    @staticmethod
    def of(source_path: str, sim_year: int):
        """Build a source from given path."""
        if source_path.startswith("s3://"):
            return S3Source(source_path, sim_year)
        else:
            return LocalFilesystemSource(source_path, sim_year)

    @abstractmethod
    def source_timestamp(self) -> int:
        """
        :return: last modification timestamp of source
        """
        pass

    @abstractmethod
    def load(self) -> str:
        """Load source and store it on local filesystem.

        :return: path to locally loaded file
        """
        pass


class LocalFilesystemSource(Source):
    """A source from local file."""

    def __init__(self, source_path: str, sim_year: int):
        super().__init__(source_path, sim_year)

    def source_timestamp(self) -> int:
        return int(os.path.getmtime(self.source_path))

    def load(self) -> str:
        return self.source_path


class S3Source(Source):
    """A source build from a S3 object.

    To use it against a private source, make sure that either:
    - AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY and AWS_DEFAULT_REGION env vars are set
    - or this process is running on an AWS EC2/ECS instance with appropriate S3 permissions
    """

    def __init__(self, source_path: str, sim_year: int):
        super().__init__(source_path, sim_year)
        self.s3 = boto3.resource("s3")
        parsed = urlparse(source_path)
        self.bucket = parsed.netloc
        self.key = parsed.path[1:]

    def source_timestamp(self) -> int:
        object_summary = self.s3.ObjectSummary(self.bucket, self.key)
        return int(object_summary.last_modified.timestamp())

    def load(self) -> str:
        tmp_path = os.path.join(tempfile.gettempdir(), self.key.replace("/", "_"))
        self.s3.Bucket(self.bucket).download_file(self.key, tmp_path)
        return tmp_path
