from datetime import datetime, timedelta
from typing import Optional

import pandas as pd
from pandas import DataFrame


def process_csv(df: DataFrame, sim_year: int) -> DataFrame:
    """Applies necessary transformations to E+ csv output.

    :param df:
    :param sim_year:
    :return:
    """
    # make a nice datetime format out of Date/Time column
    output = df.copy()
    output["Date/Time"] = output["Date/Time"].apply(
        lambda strd: process_energyplus_datetime(strdate=strd, sim_year=sim_year)
    )
    output["Date/Time"] = pd.to_datetime(output["Date/Time"], format="%Y/%m/%d  %H:%M:%S", utc=True)
    output.index = output["Date/Time"]
    # last column has a trailing space
    output.columns = [c.strip() for c in output.columns]
    # when source contains variables/meters reported at different frequency, rows contain NaNs
    # TODO: we only have numerical values but filling with 0.0 isn't always the right choice
    # example: discrete on/off schedule value reported at lower frequency will have zeros when ones are expected
    output = output.fillna(0.0)
    return output


def process_energyplus_datetime(strdate: str, sim_year: int) -> str:
    """
    transforms:
        - EnergyPlus date format '%m/%d %H:%M:%S' to '%Y/%m/%d %H:%M:%S'.
        - midnight expressed as 24:00 into 00:00

    :param strdate: the date to transform
    :param sim_year: simulation year to apply
    :return:
    """
    if month := is_month_full_name(strdate):
        return f"{sim_year:04d}/{month.month:02d}/{1:02d}  00:00:00"
    elif "24:00" in strdate:
        date = strdate.strip().split(" ")[0]
        new_date = datetime.strptime(date, "%m/%d") + timedelta(days=1)
        return f"{sim_year:04d}/{new_date.month:02d}/{new_date.day:02d}  00:00:00"
    else:
        concat = f"{sim_year:04d}/{strdate.strip()}"
        # manage 'daily' reporting frequency
        if " " not in concat:
            concat += "  00:00:00"
        return concat


def is_month_full_name(strdate: str) -> Optional[datetime]:
    try:
        return datetime.strptime(strdate, "%B")
    except ValueError:
        return None
