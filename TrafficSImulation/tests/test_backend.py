import unittest

from app.routes import plan_route


class RoutePlanningTests(unittest.TestCase):
    def setUp(self):
        self.payload = {"origin": "Downtown Austin", "destination": "Austin Airport", "mode": "simulated", "heatmap": "congestion", "hour": 12, "weather": 0, "congestion": 40, "demand": 50}

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


if __name__ == "__main__":
    unittest.main()
