import os
import tempfile
from abc import ABC, abstractmethod
from urllib.parse import urlparse

import boto3
import pandas as pd
from pandas import DataFrame

from grafener.energyplus import process_csv


class Source(ABC):
    """an abstract source"""

    def __init__(self, source_path: str):
        self.source_path = source_path

    def read_source(self) -> DataFrame:
        return process_csv(pd.read_csv(self.load()))

    @staticmethod
    def of(source_path: str):
        """build a source from given path"""
        if source_path.startswith("s3://"):
            return S3Source(source_path)
        else:
            return LocalFilesystemSource(source_path)

    @abstractmethod
    def source_timestamp(self) -> int:
        """
        :return: last modification timestamp of source
        """
        pass

    @abstractmethod
    def load(self) -> str:
        """
        load source and store it on local filesystem

        :return: path to locally loaded file
        """
        pass


class LocalFilesystemSource(Source):
    """a source from local file"""

    def __init__(self, source_path: str):
        super().__init__(source_path)

    def source_timestamp(self) -> int:
        return int(os.path.getmtime(self.source_path))

    def load(self) -> str:
        return self.source_path


class S3Source(Source):
    """
    A source build from a S3 object

    To use it against a private source, make sure that either:
    - AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY and AWS_DEFAULT_REGION env vars are set
    - or this process is running on an AWS EC2/ECS instance with appropriate S3 permissions
    """

    def __init__(self, source_path: str):
        super().__init__(source_path)
        self.s3 = boto3.resource("s3")
        parsed = urlparse(source_path)
        self.bucket = parsed.netloc
        self.key = parsed.path[1:]
        print(self.bucket, self.key)

    def source_timestamp(self) -> int:
        object_summary = self.s3.ObjectSummary(self.bucket, self.key)
        return object_summary.last_modified

    def load(self) -> str:
        tmp_path = os.path.join(tempfile.gettempdir(), self.key.replace("/", "_"))
        self.s3.Bucket(self.bucket).download_file(self.key, tmp_path)
        return tmp_path
