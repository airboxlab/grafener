import unittest

import numpy as np
import pandas as pd

from grafener.energyplus import process_csv


class TestEnergyPlusDataProcessing(unittest.TestCase):

    def test_sim_year(self):
        df = pd.DataFrame.from_dict({"Date/Time": [" 01/01  00:15:00", " 01/01  00:30:00", " 01/01  00:45:00"],
                                     "Value": np.arange(3)})
        df_2020 = process_csv(df, sim_year=2020)
        self.assertEqual(np.datetime64('2020-01-01T00:15:00.000000000'), df_2020.index.values[0])
        df_2021 = process_csv(df, sim_year=2021)
        self.assertEqual(np.datetime64('2021-01-01T00:15:00.000000000'), df_2021.index.values[0])

    def test_timestep_reporting_date_processing(self):
        df = pd.DataFrame.from_dict({"Date/Time": [" 01/01  00:15:00", " 01/01  00:30:00", " 01/01  00:45:00"],
                                     "Value": np.arange(3)})
        df = process_csv(df, sim_year=2021)
        self.assertEqual(3, len(df))
        self.assertEqual(np.datetime64('2021-01-01T00:15:00.000000000'), df.index.values[0])

    def test_monthly_reporting_date_processing(self):
        df = pd.DataFrame.from_dict({"Date/Time": ["January", "February", "March"],
                                     "Value": np.arange(3)})
        df = process_csv(df, sim_year=2021)
        self.assertEqual(3, len(df))
        for i in range(1, 4):
            self.assertEqual(np.datetime64('2021-0{}-01T00:00:00.000000000'.format(i)), df.index.values[i - 1])

    def test_daily_reporting_date_processing(self):
        df = pd.DataFrame.from_dict({"Date/Time": ["01/01", "01/02", "01/03"],
                                     "Value": np.arange(3)})
        df = process_csv(df, sim_year=2021)
        self.assertEqual(3, len(df))
        for i in range(1, 4):
            self.assertEqual(np.datetime64('2021-01-0{}T00:00:00.000000000'.format(i)), df.index.values[i - 1])
