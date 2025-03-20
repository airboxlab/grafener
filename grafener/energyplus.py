import logging
from datetime import datetime, timedelta

import pandas as pd


def process_csv(
    df: pd.DataFrame,
    sim_year: int,
    drop_duplicated: str | None = "Date/Time",
    no_tz: bool = False,
) -> pd.DataFrame:
    """Applies necessary transformations to E+ csv output.

    :param df: the DataFrame to process
    :param sim_year: simulation year to apply
    :param drop_duplicated: columns to drop if duplicated. Default: Date/Time. Strategy:
        keep last.
    :param no_tz: remove timezone information from index
    :return: a processed DataFrame
    """
    # let's not copy (keep low memory footprint)
    output = df
    # make a nice datetime format out of Date/Time column
    output["Date/Time"] = output["Date/Time"].apply(
        lambda strd: process_energyplus_datetime(strdate=strd, sim_year=sim_year)
    )
    output["Date/Time"] = pd.to_datetime(output["Date/Time"], format="%Y/%m/%d  %H:%M:%S", utc=True)
    output.index = output["Date/Time"]
    if no_tz:
        output.index = output.index.tz_convert(None)
    if drop_duplicated:
        output = output.drop_duplicates(subset=drop_duplicated, keep="last")
    # last column has a trailing space
    output.columns = [c.strip() for c in output.columns]
    # when source contains variables/meters reported at different frequency, rows contain NaNs
    # TODO: we only have numerical values but filling with 0.0 isn't always the right choice
    # example: discrete on/off schedule value reported at lower frequency will have zeros when ones are expected
    output = output.fillna(0.0)
    output = output.sort_index()
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
        try:
            new_date = datetime.strptime(f"{sim_year}/{date}", "%Y/%m/%d") + timedelta(days=1)
            return f"{sim_year:04d}/{new_date.month:02d}/{new_date.day:02d}  00:00:00"
        except ValueError as e:
            logging.error(f"error parsing {date}", exc_info=True)
            raise e
    else:
        concat = f"{sim_year:04d}/{strdate.strip()}"
        if " " not in concat:
            concat += "  00:00:00"
        return concat


def is_month_full_name(strdate: str) -> datetime | None:
    try:
        return datetime.strptime(strdate, "%B")
    except ValueError:
        return None
