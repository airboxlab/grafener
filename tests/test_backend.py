import json
import unittest

from grafener import source_reader
from grafener.backend import app
from grafener.source_reader import data_cache


class TestBackend(unittest.TestCase):
    app = app
    app.testing = True

    def test_no_source(self):
        with app.test_client() as client:
            rv = client.get("/")
            self.assertEqual("HTTP header 'source' not found", rv.data.decode("utf-8"))
            self.assertEqual(400, rv.status_code)
            rv = client.post("/search")
            self.assertEqual("HTTP header 'source' not found", rv.data.decode("utf-8"))
            self.assertEqual(400, rv.status_code)
            rv = client.post("/query")
            self.assertEqual("HTTP header 'source' not found", rv.data.decode("utf-8"))
            self.assertEqual(400, rv.status_code)

    def test_source_file_not_found(self):
        with app.test_client() as client:
            rv = client.get("/", headers={"source": "/path/to/nowhere"})
            self.assertEqual("couldn't find source [/path/to/nowhere]", rv.data.decode("utf-8"))
            self.assertEqual(400, rv.status_code)

    def test_get_metrics(self):
        with app.test_client() as client:
            rv = client.post("/search", headers={"source": "tests/test_eplusout.csv.gz"})
            json_resp = json.loads(rv.data)
            self.assertTrue(isinstance(json_resp, list))
            self.assertNotIn("Date/Time", json_resp)
            self.assertIn("Environment:Site Outdoor Air Drybulb Temperature [C](TimeStep)", json_resp)

    def test_get_metrics_with_search(self):
        with app.test_client() as client:
            rv = client.post("/search",
                             data=json.dumps({"target": "FLOOR 4 CORE"}),
                             headers={
                                 "source": "tests/test_eplusout.csv.gz",
                                 "content-type": "application/json"
                             })
            json_resp = json.loads(rv.data)
            for m in json_resp:
                self.assertIn("FLOOR 4 CORE", m)

    def test_data_cache(self):
        with app.test_client() as client:
            self.assertEqual(0, len(data_cache))
            rv = client.post("/search", headers={"source": "tests/test_eplusout.csv.gz"})
            self.assertEqual(1, len(data_cache))
            cached_value = list(data_cache.values())[0]
            self.assertTrue(cached_value.timestamp > 0)
            self.assertTrue(len(cached_value.data_frame) > 0)

    def test_timeseries_query(self):
        with app.test_client() as client:
            source_reader.PINNED_SIM_YEAR = 2020
            rv = client.post("/query",
                             data=json.dumps({
                                 "range": {
                                     "from": "2020-01-01T00:00:00.000Z",
                                     "to": "2020-02-01T00:00:00.000Z",
                                 },
                                 "interval": "30s",
                                 "intervalMs": 30000,
                                 "maxDataPoints": 550,
                                 "targets": [
                                     {
                                         "target": "Environment:Site Outdoor Air Drybulb Temperature [C](TimeStep)",
                                         "refId": "A",
                                         "type": "timeserie"
                                     }
                                 ]
                             }),
                             headers={
                                 "source": "tests/test_eplusout.csv.gz",
                                 "content-type": "application/json"
                             })
            json_resp = json.loads(rv.data)
            self.assertEqual(1, len(json_resp))
            self.assertTrue(len(json_resp[0]["datapoints"]) > 0)
            for value, ts in json_resp[0]["datapoints"]:
                self.assertIsInstance(value, float)
                self.assertIsInstance(ts, int)
            self.assertEqual("Environment:Site Outdoor Air Drybulb Temperature [C](TimeStep)", json_resp[0]["target"])

    def test_table_query(self):
        with app.test_client() as client:
            source_reader.PINNED_SIM_YEAR = 2020
            rv = client.post("/query",
                             data=json.dumps({
                                 "range": {
                                     "from": "2020-01-01T00:00:00.000Z",
                                     "to": "2020-02-01T00:00:00.000Z",
                                 },
                                 "interval": "30s",
                                 "intervalMs": 30000,
                                 "maxDataPoints": 550,
                                 "targets": [
                                     {
                                         "target": "Environment:Site Outdoor Air Drybulb Temperature [C](TimeStep)",
                                         "type": "table"
                                     },
                                     {
                                         "target": "FLOOR 4 CORE:Zone Air Temperature [C](TimeStep)",
                                         "type": "table"
                                     }
                                 ]
                             }),
                             headers={
                                 "source": "tests/test_eplusout.csv.gz",
                                 "content-type": "application/json"
                             })
            json_resp = json.loads(rv.data)
            self.assertEqual(1, len(json_resp))
            data = json_resp[0]
            self.assertEqual([
                {"text": "Time", "type": "time"},
                {"text": "Environment:Site Outdoor Air Drybulb Temperature [C](TimeStep)", "type": "number"},
                {"text": "FLOOR 4 CORE:Zone Air Temperature [C](TimeStep)", "type": "number"}
            ], data["columns"])
            self.assertTrue(len(data["rows"]) > 0)
            self.assertEqual(3, len(data["rows"][0]))
