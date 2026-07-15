const places = {
  'downtown austin': { x: 500, y: 330 }, 'ut austin': { x: 490, y: 218 },
  'austin airport': { x: 795, y: 495 }, 'the domain': { x: 505, y: 72 },
  'zilker park': { x: 392, y: 390 }, mueller: { x: 650, y: 225 },
  'south congress': { x: 520, y: 485 }, 'round rock': { x: 610, y: 20 },
  'cedar park': { x: 315, y: 35 }, 'east austin': { x: 675, y: 342 },
  'barton springs': { x: 350, y: 405 }, 'current location': { x: 455, y: 305 },
};
const aliases = { downtown: 'downtown austin', airport: 'austin airport', aus: 'austin airport', ut: 'ut austin', domain: 'the domain', zilker: 'zilker park', soco: 'south congress', east: 'east austin', barton: 'barton springs', roundrock: 'round rock' };
const title = value => value.replace(/\b\w/g, letter => letter.toUpperCase());
const clamp = (value, low, high) => Math.max(low, Math.min(high, Number(value)));
const round = (value, digits = 1) => Number(value.toFixed(digits));

function geocode(value) {
  let key = String(value || '').trim().toLowerCase().replace(/\s+/g, ' ');
  key = aliases[key] || key;
  if (!places[key]) throw new Error(`Unknown location "${value}". Try Downtown Austin, UT Austin, Austin Airport, The Domain, Zilker Park, or Mueller.`);
  return { name: title(key), point: places[key] };
}

function timeFactor(hour) {
  if ((hour >= 7 && hour <= 9) || (hour >= 16 && hour <= 18)) return 1.22;
  if (hour < 6 || hour >= 22) return 0.92;
  return 1;
}

function heatmapGrid(congestion, demand, hour, mode) {
  const cells = [];
  for (let row = 0; row < 5; row += 1) for (let column = 0; column < 8; column += 1) {
    const wave = (Math.sin(column * 1.31 + row * .77 + hour * .13) + 1) * 16;
    const center = Math.max(0, 28 - Math.hypot(column - 4, row - 2) * 8);
    let value = congestion * .66 + wave + center * .35;
    if (mode === 'demand') value = demand * .62 + wave + center;
    if (mode === 'profitability') value = demand * .72 + wave + center - congestion * .25;
    cells.push({ row, column, value: Math.round(clamp(value, 3, 100)) });
  }
  return cells;
}

function planRoute(payload) {
  const mode = payload.mode === 'realtime' ? 'realtime' : 'simulated';
  const hour = clamp(payload.hour ?? 17, 0, 23);
  let weatherLevel = clamp(payload.weather ?? 1, 0, 3);
  let congestion = clamp(payload.congestion ?? 56, 0, 100);
  let demand = clamp(payload.demand ?? 68, 0, 100);
  if (mode === 'realtime') { congestion = 44; demand = 52; weatherLevel = 0; }
  const origin = geocode(payload.origin);
  const destination = geocode(payload.destination);
  if (origin.name === destination.name) throw new Error('Origin and destination must be different.');

  const dx = destination.point.x - origin.point.x, dy = destination.point.y - origin.point.y;
  const length = Math.max(Math.hypot(dx, dy), 1);
  const normal = { x: -dy / length, y: dx / length };
  const midpoint = { x: (origin.point.x + destination.point.x) / 2, y: (origin.point.y + destination.point.y) / 2 };
  const baseDistance = length * .018 + .8;
  const weatherLabels = ['Clear', 'Light rain', 'Heavy rain', 'Severe'];
  const weatherMultipliers = [1, 1.08, 1.18, 1.32];
  const tf = timeFactor(hour), wf = weatherMultipliers[weatherLevel];
  const roadNames = ['Lamar Blvd', 'I-35', 'MoPac Expressway', 'Airport Blvd', 'Riverside Dr', 'Congress Ave'];
  const routeNames = ['Fastest', 'Balanced', 'Low traffic'], colors = ['#55d6be', '#ffb35c', '#8aa8ff'];
  const routes = [0, 68, -92].map((offset, index) => {
    const distance = round(baseDistance * (1 + index * .09));
    const baseEta = round(distance / [34, 38, 42][index] * 60 + 2);
    const routeCongestion = Math.max(4, congestion - index * 9);
    const adjustedEta = round(baseEta * (1 + routeCongestion / 180) * wf * tf);
    const subtotal = 2.2 + distance * 1.28 + adjustedEta * .31;
    const factors = {
      base_and_route: round(subtotal, 2), demand_multiplier: round(1 + Math.max(0, demand - 40) / 150, 2),
      congestion_multiplier: round(1 + routeCongestion / 500, 2), weather_multiplier: round(1 + weatherLevel * .035, 2), time_multiplier: round(tf, 2),
    };
    const estimatedPrice = round(Math.max(7.5, subtotal * factors.demand_multiplier * factors.congestion_multiplier * factors.weather_multiplier * factors.time_multiplier), 2);
    const names = [roadNames[(index * 2) % roadNames.length], roadNames[(index * 2 + 1) % roadNames.length]];
    const segments = names.map((name, segmentIndex) => {
      const local = clamp(routeCongestion + segmentIndex * 11 - index * 9, 5, 98);
      const speedLimit = [45, 55][segmentIndex];
      return { name, length_miles: round(distance * [0.47, 0.53][segmentIndex]), lanes: [3, 4][segmentIndex], speed_limit_mph: speedLimit, average_speed_mph: round(Math.max(8, speedLimit * (1 - local * .0065) / wf)), volume_vehicles_hour: Math.round(550 + local * 21), congestion: round(local / 100, 2) };
    });
    return { id: `route-${index + 1}`, name: routeNames[index], color: colors[index], distance_miles: distance, base_eta_minutes: baseEta, adjusted_eta_minutes: adjustedEta, estimated_price: estimatedPrice, congestion_score: routeCongestion, demand_score: demand, points: [origin.point, { x: midpoint.x + normal.x * offset, y: midpoint.y + normal.y * offset }, destination.point], segments, factors, data_source: mode === 'realtime' ? 'Local reference model' : 'Simulated scenario' };
  });
  const recommended = [...routes].sort((a, b) => a.adjusted_eta_minutes + a.estimated_price * .32 - b.adjusted_eta_minutes - b.estimated_price * .32)[0];
  const heatmap = ['congestion', 'demand', 'profitability', 'off'].includes(payload.heatmap) ? payload.heatmap : 'congestion';
  return { origin: origin.name, destination: destination.name, mode, weather: { severity: weatherLevel, label: weatherLabels[weatherLevel], time_multiplier: wf, source: 'Simulated fallback' }, hour, congestion, demand, routes, recommended_route_id: recommended.id, heatmap: { mode: heatmap, cells: heatmap === 'off' ? [] : heatmapGrid(congestion, demand, hour, heatmap) }, notice: mode === 'realtime' ? 'External traffic APIs are not configured; reference mode uses stable local baseline data.' : 'Traffic, demand, weather, and prices are simulated planning estimates.' };
}

module.exports = { planRoute, geocode, timeFactor, heatmapGrid };
