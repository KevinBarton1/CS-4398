import unittest
from unittest.mock import patch

from app.api.routes import plan_route
from app.map.google_places import resolve_place
from app.map.google_routes import compute_route_options
from app.map.local import build_route_options as local_build_route_options
from app.map.polyline import decode_polyline
from app.map.projection import project_lat_lng
from app.map.types import ResolvedPlace
from app.simulation.traffic import bpr_adjusted_time


class RoutePlanningTests(unittest.TestCase):
    def setUp(self):
        self.payload = {
            "origin": "Downtown Austin",
            "destination": "Austin Airport",
            "mode": "simulated",
            "heatmap": "congestion",
            "hour": 12,
            "weather": 0,
            "congestion": 40,
            "demand": 50,
        }

    def test_route_options_have_segments(self):
        result = plan_route(self.payload)
        self.assertEqual(3, len(result["routes"]))
        self.assertTrue(all(route["segments"] for route in result["routes"]))

    def test_adverse_conditions_increase_eta(self):
        clear = plan_route(self.payload)["routes"][0]
        severe = plan_route({**self.payload, "weather": 3, "congestion": 90})["routes"][0]
        self.assertGreater(severe["adjusted_eta_minutes"], clear["adjusted_eta_minutes"])

    def test_invalid_location_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "Unknown location"):
            plan_route({**self.payload, "destination": "Mars Colony"})

    def test_bpr_zero_flow_equals_free_flow(self):
        self.assertEqual(10, bpr_adjusted_time(10, 0, 1000))

    def test_bpr_time_is_monotonic_with_flow(self):
        low = bpr_adjusted_time(10, 300, 1000)
        high = bpr_adjusted_time(10, 900, 1000)
        self.assertGreater(high, low)

    def test_pricing_breakdown_reproduces_final_estimate(self):
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

    def test_weather_increases_eta_monotonically(self):
        eta = [
            plan_route({**self.payload, "weather": severity})["routes"][0]["adjusted_eta_minutes"]
            for severity in range(4)
        ]
        self.assertEqual(eta, sorted(eta))


class GoogleIntegrationTests(unittest.TestCase):
    def test_local_fallback_without_api_key(self):
        with patch("app.map.google_places.GOOGLE_MAPS_API_KEY", ""):
            place = resolve_place("Downtown Austin")
        self.assertEqual("local", place.source)
        self.assertEqual("Downtown Austin", place.name)

    def test_current_location_stays_local_even_with_api_key(self):
        with patch("app.map.google_places.GOOGLE_MAPS_API_KEY", "test-key"):
            with patch("app.map.google_places.search_place") as search_mock:
                place = resolve_place("Current location")
        search_mock.assert_not_called()
        self.assertEqual("local", place.source)
        self.assertEqual("Current Location", place.name)

    def test_google_places_used_when_available(self):
        google_place = ResolvedPlace(
            name="Downtown Austin, TX",
            latitude=30.2672,
            longitude=-97.7431,
            point=project_lat_lng(30.2672, -97.7431),
            source="google",
        )
        with patch("app.map.google_places.search_place", return_value=google_place):
            place = resolve_place("123 Congress Ave, Austin")
        self.assertEqual("google", place.source)

    def test_routes_fallback_to_local_when_google_unavailable(self):
        origin = ResolvedPlace("Downtown Austin", 0, 0, project_lat_lng(30.27, -97.74), "local")
        destination = ResolvedPlace("Austin Airport", 0, 0, project_lat_lng(30.20, -97.67), "local")
        with patch("app.map.google_routes.GOOGLE_MAPS_API_KEY", ""):
            routes = compute_route_options(origin, destination)
        self.assertIsNone(routes)

        _, _, local_routes = local_build_route_options("Downtown Austin", "Austin Airport")
        self.assertEqual(3, len(local_routes))
        self.assertEqual("local", local_routes[0]["map_source"])

    def test_google_routes_parsed_when_available(self):
        origin = ResolvedPlace("Downtown Austin", 30.27, -97.74, project_lat_lng(30.27, -97.74), "google")
        destination = ResolvedPlace("Austin Airport", 30.20, -97.67, project_lat_lng(30.20, -97.67), "google")
        mock_response = {
            "routes": [
                {
                    "distanceMeters": 16093,
                    "staticDuration": "1200s",
                    "duration": "150divs",
                    "polyline": {"encodedPolyline": "_p~iF~ps|U_ulLnnqC_mqNvxq`@"},
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
        # Fix typo in mock - duration should be valid
        mock_response["routes"][0]["duration"] = "1500s"

        with patch("app.map.google_routes.GOOGLE_MAPS_API_KEY", "test-key"):
            with patch("httpx.post") as post_mock:
                post_mock.return_value.raise_for_status = lambda: None
                post_mock.return_value.json.return_value = mock_response
                routes = compute_route_options(origin, destination)

        self.assertIsNotNone(routes)
        self.assertEqual(1, len(routes))
        self.assertEqual("google", routes[0]["map_source"])
        self.assertGreater(routes[0]["distance_miles"], 0)
        self.assertEqual("Congress Ave", routes[0]["road_names"][0])

    def test_polyline_decoder_returns_coordinates(self):
        decoded = decode_polyline("_p~iF~ps|U_ulLnnqC_mqNvxq`@")
        self.assertGreaterEqual(len(decoded), 2)
        self.assertIsInstance(decoded[0][0], float)


if __name__ == "__main__":
    unittest.main()
