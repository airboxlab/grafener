import unittest

from docker.rootfs.usr.local.bin.backend import app


class TestFoo(unittest.TestCase):
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
