import unittest
from unittest import mock
from unittest.mock import patch
import datetime

from app import create_app


class MockResponse:
    def __init__(self, json_data, status_code):
        self.json_data = json_data
        self.status_code = status_code

    def json(self):
        return self.json_data


def mocked_requests_get(*args, **kwargs):
    if args[0] == "https://tle.ivanstanojevic.me/api/tle/25544":
        tmp_response = {
            "@context": "https:\\/\\/www.w3.org\\/ns\\/hydra\\/context.jsonld",
            "@id": "https:\\/\\/tle.ivanstanojevic.me\\/api\\/tle\\/25544",
            "@type": "Tle",
            "satelliteId": 25544,
            "name": "ISS (ZARYA)",
            "date": "2026-06-07T21:37:51+00:00",
            "line1": "1 25544U 98067A   26158.90128687  .00007994  00000+0  14961-3 0  9995",
            "line2": "2 25544  51.6338 346.0598 0006926 145.2709 214.8733 15.49660544570312",
        }
        return MockResponse(tmp_response, 200)

    elif args[0] == "https://tle.ivanstanojevic.me/api/tle/0":
        tmp_response = {
            "response": {
                "message": "Unable to find record with id 0"
            }
        }
        return MockResponse(tmp_response, 404)

    return MockResponse(None, 404)


class MainTestCase(unittest.TestCase):

    def setUp(self):
        self.app = create_app("testing")
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = self.app.test_client()

    def tearDown(self):
        self.app_context.pop()

    def test_index_page(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Earth", response.data)

    def test_calculate_get_page(self):
        response = self.client.get("/calculate")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Calculate", response.data)

    @mock.patch("app.main.views.requests.get", side_effect=mocked_requests_get)
    def test_calculate(self, mock_get):
        response = self.client.post("/calculate", data={
            "input_date_time": datetime.datetime(2026, 6, 1, 12, 0)
        })

        self.assertTrue(
            "Position (X, Y, Z) in km: (888.7196363510753, -4143.88732612825, -5323.6785654496225)"
            in response.get_data(as_text=True)
        )

    @patch("app.main.views.parse_satellite")
    @patch("app.main.views.requests.get")
    def test_calculate_success_shows_tle_datetime(self, mock_get, mock_parse_satellite):
        mock_get.return_value = MockResponse({
            "satelliteId": 25544,
            "name": "ISS",
            "date": "2026-06-01T15:35:00+00:00",
            "line1": "1 25544U 98067A   26152.64930556  .00000000  00000-0  00000-0 0  9991",
            "line2": "2 25544  51.6400 100.0000 0001000 100.0000 100.0000 15.50000000    10",
        }, 200)

        mock_parse_satellite.return_value = (0, [1, 2, 3], [4, 5, 6])

        response = self.client.post("/calculate", data={
            "input_date_time": "2026-06-01T15:35"
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"TLE DateTime: 01.06.2026 15.35", response.data)
        self.assertIn(
            b"Satellite/space object position and velocity calculated",
            response.data
        )

    @patch("app.main.views.requests.get")
    def test_calculate_api_error(self, mock_get):
        mock_get.return_value = MockResponse({}, 404)

        response = self.client.post("/calculate", data={
            "input_date_time": "2026-06-01T15:35"
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Something went wrong. Try again.", response.data)

    @patch("app.main.views.parse_satellite")
    @patch("app.main.views.requests.get")
    def test_calculate_satellite_error(self, mock_get, mock_parse_satellite):
        mock_get.return_value = MockResponse({
            "satelliteId": 25544,
            "name": "ISS",
            "date": "2026-06-01T15:35:00+00:00",
            "line1": "1 25544U 98067A   26152.64930556  .00000000  00000-0  00000-0 0  9991",
            "line2": "2 25544  51.6400 100.0000 0001000 100.0000 100.0000 15.50000000    10",
        }, 200)

        mock_parse_satellite.return_value = (1, None, None)

        response = self.client.post("/calculate", data={
            "input_date_time": "2026-06-01T15:35"
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Something went wrong. Try again.", response.data)