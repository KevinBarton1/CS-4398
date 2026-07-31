interface HeatmapLegendProps {
  notice: string;
}

const LEGEND_STOPS = [
  { label: "Low", value: 20 },
  { label: "Moderate", value: 50 },
  { label: "High", value: 80 },
];

export function HeatmapLegend({ notice }: HeatmapLegendProps) {
  return (
    <aside className="heatmap-legend" aria-label="Congestion heatmap legend">
      <strong>Simulated congestion</strong>
      <p className="heatmap-legend__note">{notice}</p>
      <ul className="heatmap-legend__scale">
        {LEGEND_STOPS.map((stop) => (
          <li key={stop.label}>
            <span
              className="heatmap-legend__swatch"
              style={{
                backgroundColor:
                  stop.value >= 70 ? "#ff5c45" : stop.value >= 40 ? "#ffb35c" : "#55d6be",
                opacity: stop.value / 100,
              }}
              aria-hidden="true"
            />
            <span>{`${stop.label} (${stop.value})`}</span>
          </li>
        ))}
      </ul>
      <p className="visually-hidden">
        Congestion intensity ranges from 0 to 100. Values are simulated planning estimates, not live
        observations.
      </p>
    </aside>
  );
}
