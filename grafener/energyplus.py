import logging
import os
from datetime import datetime, timedelta

import pandas as pd
from pandas import DataFrame

# EnergyPlus date format doesn't include year by default
PINNED_SIM_YEAR = int(os.getenv("SIM_YEAR", datetime.now().year))
logging.info("Using pinned simulation year: {}".format(PINNED_SIM_YEAR))


def process_csv(df: DataFrame) -> DataFrame:
    """
    applies necessary transformations to E+ csv output

    :param df:
    :return:
    """
    # make a nice datetime format out of Date/Time column
    df["Date/Time"] = df["Date/Time"].apply(process_energyplus_datetime)
    df["Date/Time"] = pd.to_datetime(df["Date/Time"], format="%Y/%m/%d  %H:%M:%S", utc=True)
    df.index = df["Date/Time"]
    # last column has a trailing space
    df.columns = [c.strip() for c in df.columns]
    # when source contains variables/meters reported at different frequency, rows contain NaNs
    # TODO: we only have numerical values but filling with 0.0 isn't always the right choice
    # example: discrete on/off schedule value reported at lower frequency will have zeros when ones are expected
    df = df.fillna(0.0)
    return df


def process_energyplus_datetime(strdate: str) -> str:
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
