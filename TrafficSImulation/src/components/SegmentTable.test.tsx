import React from "react";
import { render, screen } from "@testing-library/react";
import { SegmentTable } from "./SegmentTable";
import { makeRoute, makeSegment } from "../test/fixtures";

describe("SegmentTable", () => {
  test("T-39 renders every segment field with units and textual severity", () => {
    const route = makeRoute({
      name: "Balanced",
      segments: [
        makeSegment({
          name: "Congress Ave",
          length_miles: 2.1,
          lanes: 2,
          speed_limit_mph: 35,
          average_speed_mph: 22.4,
          volume_vehicles_hour: 18400,
          capacity_vehicles_hour: 22000,
          congestion: 0.734,
          free_flow_minutes: 3.2,
          adjusted_minutes: 4.6,
          traffic_ratio: 1.44,
        }),
        makeSegment({
          name: "Riverside Dr",
          length_miles: 1.5,
          lanes: 3,
          speed_limit_mph: 45,
          average_speed_mph: 40.1,
          volume_vehicles_hour: 9200,
          capacity_vehicles_hour: 15600,
          congestion: 0.18,
          free_flow_minutes: 2.0,
          adjusted_minutes: 2.3,
          traffic_ratio: 1.15,
        }),
        makeSegment({
          name: "Airport Blvd",
          length_miles: 4.2,
          lanes: 4,
          speed_limit_mph: 55,
          average_speed_mph: 48.0,
          volume_vehicles_hour: 11200,
          capacity_vehicles_hour: 24000,
          congestion: 0.42,
          free_flow_minutes: 4.8,
          adjusted_minutes: 5.9,
          traffic_ratio: 1.23,
        }),
      ],
    });

    render(<SegmentTable route={route} />);

    const rows = screen.getAllByRole("row").slice(1);
    expect(rows).toHaveLength(3);

    expect(screen.getByText("Congress Ave")).toBeInTheDocument();
    expect(screen.getByText("2 lanes · 73% congestion")).toBeInTheDocument();
    expect(screen.getByText("2.1 mi")).toBeInTheDocument();
    expect(screen.getByText("22.4 mph")).toBeInTheDocument();
    expect(screen.getByText("limit 35")).toBeInTheDocument();
    expect(screen.getByText("18,400 veh/hr")).toBeInTheDocument();
    expect(screen.getByText("of 22,000 veh/hr capacity")).toBeInTheDocument();
    expect(screen.getByText("4.6 min")).toBeInTheDocument();
    expect(screen.getByText("free flow 3.2 min")).toBeInTheDocument();
    expect(screen.getByText("x1.44")).toBeInTheDocument();
    expect(screen.getAllByText("of free-flow time")).toHaveLength(3);

    expect(screen.getByText("Riverside Dr")).toBeInTheDocument();
    expect(screen.getByText(/18%\s*congestion/)).toBeInTheDocument();
    expect(screen.getByText("Airport Blvd")).toBeInTheDocument();
    expect(screen.getByText(/42%\s*congestion/)).toBeInTheDocument();
  });
});
