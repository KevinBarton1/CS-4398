const test = require('node:test');
const assert = require('node:assert/strict');
const { planRoute, geocode, timeFactor, heatmapGrid } = require('../tools/simulation');

const base = { origin: 'Downtown Austin', destination: 'Austin Airport', mode: 'simulated', heatmap: 'congestion', hour: 12, weather: 0, congestion: 40, demand: 50 };

test('valid locations return three route options and segment data', () => {
  const result = planRoute(base);
  assert.equal(result.routes.length, 3);
  assert.ok(result.routes.every(route => route.distance_miles > 0 && route.segments.length === 2));
  assert.ok(result.routes.some(route => route.id === result.recommended_route_id));
});
test('invalid and identical locations are rejected clearly', () => {
  assert.throws(() => geocode('Mars Colony'), /Unknown location/);
  assert.throws(() => planRoute({ ...base, destination: 'Downtown' }), /must be different/);
});
test('weather and congestion increase adjusted ETA', () => {
  const clear = planRoute(base).routes[0];
  const severe = planRoute({ ...base, weather: 3, congestion: 90 }).routes[0];
  assert.ok(severe.adjusted_eta_minutes > clear.adjusted_eta_minutes);
  assert.ok(severe.estimated_price > clear.estimated_price);
});
test('demand increases fare and demand heatmap values', () => {
  const low = planRoute({ ...base, demand: 10, heatmap: 'demand' });
  const high = planRoute({ ...base, demand: 95, heatmap: 'demand' });
  assert.ok(high.routes[0].estimated_price > low.routes[0].estimated_price);
  assert.ok(high.heatmap.cells[0].value > low.heatmap.cells[0].value);
});
test('reference mode uses stable fallback conditions', () => {
  const a = planRoute({ ...base, mode: 'realtime', congestion: 1, demand: 1 });
  const b = planRoute({ ...base, mode: 'realtime', congestion: 99, demand: 99 });
  assert.equal(a.congestion, 44); assert.equal(a.demand, 52);
  assert.equal(a.routes[0].adjusted_eta_minutes, b.routes[0].adjusted_eta_minutes);
});
test('rush-hour factor and heatmap ranges are bounded', () => {
  assert.ok(timeFactor(17) > timeFactor(12));
  const cells = heatmapGrid(100, 100, 17, 'profitability');
  assert.equal(cells.length, 40);
  assert.ok(cells.every(cell => cell.value >= 3 && cell.value <= 100));
});
