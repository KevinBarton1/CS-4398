import unittest

from app.api.routes import plan_route
from app.simulation.traffic import bpr_adjusted_time


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


if __name__ == "__main__":
    unittest.main()
