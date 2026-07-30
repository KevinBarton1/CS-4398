import httpx
import unittest
from unittest.mock import MagicMock, patch

from app.api.routes import plan_route
from app.map.google_embed import build_map_embed_url, compute_map_view, compute_map_view_for_polyline
from app.map.google_errors import format_google_api_error
from app.map.google_places import resolve_place
from app.map.google_routes import compute_route_options
from app.map.polyline import decode_polyline
from app.map.types import ResolvedPlace
from app.simulation.traffic import bpr_adjusted_time
from tests.google_mocks import mock_build_route_options, mock_google_routes


@patch("app.api.routes.build_route_options", side_effect=mock_build_route_options)
class RoutePlanningTests(unittest.TestCase):
    def setUp(self):
        self.payload = {
            "origin": "Downtown Austin",
            "destination": "Austin Airport",
            "mode": "simulated",
            "hour": 12,
            "weather": 0,
            "congestion": 40,
            "demand": 50,
        }

    def test_route_options_have_segments(self, _mock_build):
        result = plan_route(self.payload)
        self.assertEqual(3, len(result["routes"]))
        self.assertTrue(all(route["segments"] for route in result["routes"]))
        self.assertIn("map_embed_url", result)
        self.assertIn("map_view", result)
        self.assertTrue(all(route["polyline"] for route in result["routes"]))

    def test_adverse_conditions_increase_eta(self, _mock_build):
        clear = plan_route(self.payload)["routes"][0]
        severe = plan_route({**self.payload, "weather": 3, "congestion": 90})["routes"][0]
        self.assertGreater(severe["adjusted_eta_minutes"], clear["adjusted_eta_minutes"])

    def test_invalid_location_is_rejected(self, _mock_build):
        with patch("app.api.routes.build_route_options", side_effect=ValueError('Could not geocode "Mars Colony" using Google Places.')):
            with self.assertRaisesRegex(ValueError, "Could not geocode"):
                plan_route({**self.payload, "destination": "Mars Colony"})

    def test_bpr_zero_flow_equals_free_flow(self, _mock_build):
        self.assertEqual(10, bpr_adjusted_time(10, 0, 1000))

    def test_bpr_time_is_monotonic_with_flow(self, _mock_build):
        low = bpr_adjusted_time(10, 300, 1000)
        high = bpr_adjusted_time(10, 900, 1000)
        self.assertGreater(high, low)

    def test_pricing_breakdown_reproduces_final_estimate(self, _mock_build):
        route = plan_route(self.payload)["routes"][0]
        factors = route["factors"]
        reproduced = (
            factors["route_subtotal"]
            * factors["demand_multiplier"]
            * factors["traffic_multiplier"]
            * factors["weather_multiplier"]
            * factors["time_multiplier"]
        )
        self.assertAlmostEqual(route["estimated_price"], round(reproduced, 2), places=2)

    def test_weather_increases_eta_monotonically(self, _mock_build):
        eta = [
            plan_route({**self.payload, "weather": severity})["routes"][0]["adjusted_eta_minutes"]
            for severity in range(4)
        ]
        self.assertEqual(eta, sorted(eta))


class GoogleIntegrationTests(unittest.TestCase):
    def test_missing_api_key_rejects_geocoding(self):
        with patch("app.map.google_places.GOOGLE_MAPS_API_KEY", ""):
            with self.assertRaisesRegex(ValueError, "GOOGLE_MAPS_API_KEY is not configured"):
                resolve_place("Downtown Austin")

    def test_current_location_is_rejected(self):
        with patch("app.map.google_places.GOOGLE_MAPS_API_KEY", "test-key"):
            with self.assertRaisesRegex(ValueError, "Current location is not supported"):
                resolve_place("Current location")

    def test_google_places_used_when_available(self):
        google_place = ResolvedPlace(
            name="Downtown Austin, TX",
            latitude=30.2672,
            longitude=-97.7431,
            source="google",
        )
        with patch("app.map.google_places.search_place", return_value=google_place):
            place = resolve_place("123 Congress Ave, Austin")
        self.assertEqual("google", place.source)

    def test_routes_require_api_key(self):
        origin = ResolvedPlace("Downtown Austin", 30.27, -97.74, "google")
        destination = ResolvedPlace("Austin Airport", 30.20, -97.67, "google")
        with patch("app.map.google_routes.GOOGLE_MAPS_API_KEY", ""):
            with self.assertRaisesRegex(ValueError, "GOOGLE_MAPS_API_KEY is not configured"):
                compute_route_options(origin, destination)

    def test_google_routes_parsed_when_available(self):
        origin = ResolvedPlace("Downtown Austin", 30.27, -97.74, "google")
        destination = ResolvedPlace("Austin Airport", 30.20, -97.67, "google")
        mock_response = {
            "routes": [
                {
                    "distanceMeters": 16093,
                    "staticDuration": "1200s",
                    "duration": "1500s",
                    "legs": [{
                        "steps": [{
                            "distanceMeters": 8046,
                            "staticDuration": "600s",
                            "navigationInstruction": {"instructions": "Head south on Congress Ave"},
                        }],
                    }],
                }
            ]
        }

        with patch("app.map.google_routes.GOOGLE_MAPS_API_KEY", "test-key"):
            with patch("httpx.post") as post_mock:
                post_mock.return_value.raise_for_status = lambda: None
                post_mock.return_value.json.return_value = mock_response
                routes = compute_route_options(origin, destination)

        self.assertEqual(1, len(routes))
        self.assertEqual("google", routes[0]["map_source"])
        self.assertGreater(routes[0]["distance_miles"], 0)
        self.assertEqual("Congress Ave", routes[0]["road_names"][0])

    def test_google_api_error_includes_field_violations(self):
        response = MagicMock()
        response.json.return_value = {
            "error": {
                "code": 400,
                "message": "Request contains an invalid argument.",
                "status": "INVALID_ARGUMENT",
                "details": [{
                    "@type": "type.googleapis.com/google.rpc.BadRequest",
                    "fieldViolations": [{
                        "field": "departure_time",
                        "description": "departure_time is not supported for TRAFFIC_UNAWARE.",
                    }],
                }],
            },
        }
        detail = format_google_api_error(response)
        self.assertIn("Request contains an invalid argument.", detail)
        self.assertIn("departure_time: departure_time is not supported for TRAFFIC_UNAWARE.", detail)

    def test_routes_error_surfaces_field_violations(self):
        origin = ResolvedPlace("Downtown Austin", 30.27, -97.74, "google")
        destination = ResolvedPlace("Austin Airport", 30.20, -97.67, "google")
        error_response = MagicMock()
        error_response.status_code = 400
        error_response.json.return_value = {
            "error": {
                "message": "Request contains an invalid argument.",
                "details": [{
                    "@type": "type.googleapis.com/google.rpc.BadRequest",
                    "fieldViolations": [{
                        "field": "compute_alternative_routes",
                        "description": "Alternative routes are unavailable for this request.",
                    }],
                }],
            },
        }
        http_error = httpx.HTTPStatusError(
            "bad request",
            request=MagicMock(),
            response=error_response,
        )

        with patch("app.map.google_routes.GOOGLE_MAPS_API_KEY", "test-key"):
            with patch("httpx.post") as post_mock:
                post_mock.return_value.raise_for_status.side_effect = http_error
                with self.assertRaisesRegex(
                    ValueError,
                    r"compute_alternative_routes: Alternative routes are unavailable for this request\.",
                ):
                    compute_route_options(origin, destination)

    def test_routes_payload_omits_departure_time_when_traffic_unaware(self):
        origin = ResolvedPlace("Downtown Austin", 30.27, -97.74, "google")
        destination = ResolvedPlace("Austin Airport", 30.20, -97.67, "google")
        mock_response = {"routes": [{"distanceMeters": 16093, "staticDuration": "1200s", "legs": [{"steps": []}]}]}

        with patch("app.map.google_routes.GOOGLE_MAPS_API_KEY", "test-key"):
            with patch("httpx.post") as post_mock:
                post_mock.return_value.raise_for_status = lambda: None
                post_mock.return_value.json.return_value = mock_response
                compute_route_options(origin, destination, use_traffic=False)
                payload = post_mock.call_args.kwargs["json"]
                self.assertEqual("TRAFFIC_UNAWARE", payload["routingPreference"])
                self.assertNotIn("departureTime", payload)

                compute_route_options(origin, destination, use_traffic=True)
                traffic_payload = post_mock.call_args.kwargs["json"]
                self.assertEqual("TRAFFIC_AWARE", traffic_payload["routingPreference"])
                self.assertIn("departureTime", traffic_payload)


class GoogleEmbedTests(unittest.TestCase):
    def test_polyline_decoder_returns_coordinates(self):
        # Encoded polyline for two nearby Austin points.
        encoded = "_p~iF~ps|U_ulLnnqC_mqNvxq`@"
        points = decode_polyline(encoded)
        self.assertGreaterEqual(len(points), 2)
        self.assertIn("lat", points[0])
        self.assertIn("lng", points[0])

    def test_compute_map_view_for_polyline_fits_route(self):
        polyline = [
            {"lat": 30.2672, "lng": -97.7431},
            {"lat": 30.2500, "lng": -97.7200},
            {"lat": 30.1975, "lng": -97.6664},
        ]
        center_lat, center_lng, zoom = compute_map_view_for_polyline(polyline)
        self.assertAlmostEqual(center_lat, 30.23235, places=3)
        self.assertAlmostEqual(center_lng, -97.70475, places=3)
        self.assertGreaterEqual(zoom, 10)
        self.assertLessEqual(zoom, 15)

    def test_compute_map_view_centers_between_points(self):
        center_lat, center_lng, zoom = compute_map_view(30.2672, -97.7431, 30.1975, -97.6664)
        self.assertAlmostEqual(center_lat, 30.23235, places=4)
        self.assertAlmostEqual(center_lng, -97.70475, places=4)
        self.assertEqual(zoom, 13)

    @patch("app.map.google_embed.GOOGLE_MAPS_API_KEY", "test-key")
    def test_build_map_embed_url_uses_view_mode(self):
        url = build_map_embed_url(30.2324, -97.7048, 12)
        self.assertIn("https://www.google.com/maps/embed/v1/view?", url)
        self.assertIn("key=test-key", url)
        self.assertIn("center=30.2324%2C-97.7048", url)
        self.assertIn("zoom=12", url)
        self.assertIn("maptype=roadmap", url)

    @patch("app.map.google_embed.GOOGLE_MAPS_API_KEY", "")
    def test_build_map_embed_url_without_key_returns_none(self):
        self.assertIsNone(build_map_embed_url(30.0, -97.0, 12))


if __name__ == "__main__":
    unittest.main()
