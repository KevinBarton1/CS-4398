import type { RouteOption } from "../types";
import {
  formatFlow,
  formatMiles,
  formatMinutes,
  formatMultiplier,
  formatRatioPercent,
} from "../utils/format";

interface SegmentTableProps {
  route: RouteOption;
}

function formatCell(value: number | string | undefined): string {
  if (value === undefined || value === null || Number.isNaN(value as number)) {
    return "—";
  }
  return String(value);
}

export function SegmentTable({ route }: SegmentTableProps) {
  return (
    <section className="card road-detail">
      <span className="eyebrow">Road detail</span>
      <h2>Segment statistics</h2>
      <div className="table-wrap">
        <table>
          <caption>{`Segment statistics for ${route.name}`}</caption>
          <thead>
            <tr>
              <th scope="col">Road</th>
              <th scope="col">Length</th>
              <th scope="col">Speed</th>
              <th scope="col">Flow</th>
              <th scope="col">Time</th>
              <th scope="col">Delay</th>
            </tr>
          </thead>
          <tbody>
            {route.segments.map((segment, index) => (
              <tr key={`${segment.name}-${index}`}>
                <td>
                  <b>{segment.name}</b>
                  <small>
                    {segment.lanes} lanes · {formatRatioPercent(segment.congestion)} congestion
                  </small>
                </td>
                <td>{formatMiles(segment.length_miles)}</td>
                <td>
                  {formatCell(segment.average_speed_mph)} mph
                  <small>limit {formatCell(segment.speed_limit_mph)}</small>
                </td>
                <td>
                  {formatFlow(segment.volume_vehicles_hour)}
                  <small>of {formatFlow(segment.capacity_vehicles_hour)} capacity</small>
                </td>
                <td>
                  {formatMinutes(segment.adjusted_minutes)}
                  <small>free flow {formatMinutes(segment.free_flow_minutes)}</small>
                </td>
                <td>
                  {formatMultiplier(segment.traffic_ratio)}
                  <small>of free-flow time</small>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
