import type { RouteOption } from "../types";
import { formatCurrency, formatMultiplier } from "../utils/format";

interface PriceSummaryProps {
  route: RouteOption;
}

const DISCLAIMER =
  "Illustrative estimate only. Not an official Uber or Lyft fare.";

export function PriceSummary({ route }: PriceSummaryProps) {
  const factors = route.price_factors;

  return (
    <section className="card pricing">
      <div>
        <span className="eyebrow">Planning estimate</span>
        <h2>Expected fare</h2>
      </div>
      <strong>{formatCurrency(route.estimated_price)}</strong>
      <dl className="factors">
        <div>
          <dt>Route subtotal</dt>
          <dd>{formatCurrency(factors.route_subtotal)}</dd>
        </div>
        <div>
          <dt>Traffic</dt>
          <dd>{formatMultiplier(factors.traffic_multiplier)}</dd>
        </div>
        <div>
          <dt>Weather</dt>
          <dd>{formatMultiplier(factors.weather_multiplier)}</dd>
        </div>
        <div>
          <dt>Time of day</dt>
          <dd>{formatMultiplier(factors.time_multiplier)}</dd>
        </div>
        <div>
          <dt>Before rounding</dt>
          <dd>{formatCurrency(factors.unrounded_total)}</dd>
        </div>
      </dl>
      <p className="data-source">{route.data_source}</p>
      <p>{DISCLAIMER}</p>
    </section>
  );
}
