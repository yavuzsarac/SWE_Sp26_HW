import unittest
from app import create_app
from app.main.utils import build_query, parse_response, parse_satellite
import datetime

class MockResponse:
    def __init__(self, json_data, status_code):
        self.json_data = json_data
        self.status_code = status_code

    def json(self):
        return self.json_data

class UtilsTestCase(unittest.TestCase):
    def test_parse_response_success_with_date(self):
        response = MockResponse({
            "satelliteId": 25544,
            "name": "ISS",
            "date": "2026-06-01T15:35:00+00:00",
            "line1": "1 25544U 98067A   26152.64930556  .00000000  00000-0  00000-0 0  9991",
            "line2": "2 25544  51.6400 100.0000 0001000 100.0000 100.0000 15.50000000    10"
        }, 200)

        result = parse_response(response)

        self.assertEqual(result["satellite_id"], 25544)
        self.assertEqual(result["satellite_name"], "ISS")
        self.assertEqual(result["date"], "01.06.2026 15.35")
        self.assertEqual(result["msg"], "OK")

    def test_parse_response_error(self):
        response = MockResponse({}, 404)

        result = parse_response(response)

        self.assertIsNone(result)

    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        self.app_context.pop()
    
    def test_build_query(self):
        satellite_id = "000000"
        (query, headers) = build_query(satellite_id)
        self.assertEqual(query, "https://tle.ivanstanojevic.me/api/tle/000000")