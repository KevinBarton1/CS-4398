const $ = selector => document.querySelector(selector);
const $$ = selector => [...document.querySelectorAll(selector)];
const state = { mode: 'simulated', heatmap: 'congestion', selectedRouteId: null, data: null, timer: null };
const weatherLabels = ['Clear', 'Light rain', 'Heavy rain', 'Severe'];

function payload() {
  return { origin: $('#origin').value, destination: $('#destination').value, mode: state.mode, heatmap: state.heatmap, hour: Number($('#hour').value), weather: Number($('#weather').value), congestion: Number($('#congestion').value), demand: Number($('#demand').value) };
}
function showToast(message) { const toast = $('#toast'); toast.textContent = message; toast.classList.add('show'); clearTimeout(showToast.timer); showToast.timer = setTimeout(() => toast.classList.remove('show'), 4200); }
function setLoading(loading) { $('.primary-button').disabled = loading; $('.primary-button span:first-child').textContent = loading ? 'Calculating…' : 'Plan routes'; $('#system-status').textContent = loading ? 'Recalculating' : 'Simulation ready'; }
function formatHour(hour) { const suffix = hour >= 12 ? 'PM' : 'AM'; return `${hour % 12 || 12}:00 ${suffix}`; }
function updateControlOutputs() { $('#hour-output').textContent = formatHour(Number($('#hour').value)); $('#weather-output').textContent = weatherLabels[Number($('#weather').value)]; $('#congestion-output').textContent = `${$('#congestion').value}%`; $('#demand-output').textContent = `${$('#demand').value}%`; }

async function calculate({ preserveSelection = true } = {}) {
  setLoading(true);
  try {
    const response = await fetch('/api/plan', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload()) });
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || 'Route calculation failed.');
    state.data = result;
    const stillExists = result.routes.some(route => route.id === state.selectedRouteId);
    if (!preserveSelection || !stillExists) state.selectedRouteId = result.recommended_route_id;
    $('#map-empty').classList.add('hidden');
    render();
  } catch (error) { $('#map-empty').classList.remove('hidden'); showToast(error.message); }
  finally { setLoading(false); }
}

function selectedRoute() { return state.data?.routes.find(route => route.id === state.selectedRouteId) || state.data?.routes[0]; }
function routePath(points) { if (!points?.length) return ''; if (points.length === 3) return `M ${points[0].x} ${points[0].y} Q ${points[1].x} ${points[1].y} ${points[2].x} ${points[2].y}`; return points.map((point, index) => `${index ? 'L' : 'M'} ${point.x} ${point.y}`).join(' '); }
function heatColor(value) { if (value < 45) return '#35c9b0'; if (value < 72) return '#f3c45b'; return '#ff6f61'; }

function renderMap() {
  const route = selectedRoute(), data = state.data;
  $('#heatmap-layer').innerHTML = data.heatmap.cells.map(cell => `<rect class="heat-cell" x="${cell.column * 125}" y="${cell.row * 130}" width="126" height="131" rx="18" fill="${heatColor(cell.value)}" opacity="${(.05 + cell.value / 650).toFixed(2)}"><title>${data.heatmap.mode}: ${cell.value}/100</title></rect>`).join('');
  $('#route-layer').innerHTML = data.routes.slice().reverse().map(item => `<path data-route-id="${item.id}" class="route-path ${item.id === route.id ? 'route-active' : 'route-muted'}" d="${routePath(item.points)}" stroke="${item.color}" stroke-width="${item.id === route.id ? 9 : 7}"/>`).join('');
  const start = route.points[0], end = route.points.at(-1);
  $('#marker-layer').innerHTML = `<g transform="translate(${start.x} ${start.y})"><circle class="marker-pin" r="11" fill="#55d6be" stroke="#e8fffa" stroke-width="3"/><text class="marker-label" x="17" y="4">${data.origin}</text></g><g transform="translate(${end.x} ${end.y})"><path class="marker-pin" d="M0 15C-3 8-11 1-11-7a11 11 0 1 1 22 0C11 1 3 8 0 15Z" fill="#ffb35c" stroke="#fff2df" stroke-width="2"/><circle cy="-7" r="3" fill="#41250a"/><text class="marker-label" x="17" y="0">${data.destination}</text></g>`;
  const bend = route.points[1]; $('#jam-layer').innerHTML = route.congestion_score > 48 ? `<circle class="jam-pulse" cx="${bend.x}" cy="${bend.y}" r="14"/><circle class="jam-core" cx="${bend.x}" cy="${bend.y}" r="5"><title>Moving jam: low-speed, high-density segment</title></circle>` : '';
  $('#legend-label').textContent = data.heatmap.mode === 'off' ? 'Heatmap off' : `${data.heatmap.mode[0].toUpperCase() + data.heatmap.mode.slice(1)} intensity`;
  $('.map-legend').classList.toggle('hidden', data.heatmap.mode === 'off');
  $$('#route-layer [data-route-id]').forEach(path => path.addEventListener('click', () => { state.selectedRouteId = path.dataset.routeId; render(); }));
}

function renderRoutes() {
  $('#route-count').textContent = state.data.routes.length;
  $('#route-list').innerHTML = state.data.routes.map(route => `<button class="route-card ${route.id === state.selectedRouteId ? 'active' : ''}" style="--route-color:${route.color}" data-route-id="${route.id}"><div class="route-title"><span>${route.name}</span>${route.id === state.data.recommended_route_id ? '<span class="recommend">Recommended</span>' : ''}</div><div class="route-stats"><span><strong>${route.adjusted_eta_minutes}</strong> min</span><span><strong>${route.distance_miles}</strong> mi</span><span><strong>$${route.estimated_price.toFixed(2)}</strong></span></div></button>`).join('');
  $$('#route-list [data-route-id]').forEach(card => card.addEventListener('click', () => { state.selectedRouteId = card.dataset.routeId; render(); }));
}

function renderDetails() {
  const route = selectedRoute();
  $('#selected-route-name').textContent = route.name; $('#source-badge').textContent = state.data.mode === 'realtime' ? 'Local reference' : 'Simulated';
  $('#adjusted-eta').textContent = route.adjusted_eta_minutes; $('#distance').textContent = `${route.distance_miles} mi`; $('#base-eta').textContent = `${route.base_eta_minutes} min`; $('#congestion-score').textContent = `${route.congestion_score}/100`; $('#demand-score').textContent = `${route.demand_score}/100`; $('#price').textContent = `$${route.estimated_price.toFixed(2)}`;
  $('#price-factors').innerHTML = `<span>Route $${route.factors.base_and_route.toFixed(2)}</span><span>Demand ×${route.factors.demand_multiplier.toFixed(2)}</span><span>Traffic ×${route.factors.congestion_multiplier.toFixed(2)}</span><span>Weather ×${route.factors.weather_multiplier.toFixed(2)}</span><span>Time ×${route.factors.time_multiplier.toFixed(2)}</span>`;
  $('#segment-body').innerHTML = route.segments.map(segment => `<tr><td><strong>${segment.name}</strong><br>${segment.lanes} lanes · ${Math.round(segment.congestion * 100)}%</td><td>${segment.length_miles} mi</td><td>${segment.average_speed_mph} mph<br><small>limit ${segment.speed_limit_mph}</small></td><td>${segment.volume_vehicles_hour.toLocaleString()}<br><small>veh/hr</small></td></tr>`).join('');
  $('#notice').textContent = state.data.notice;
}
function render() { if (!state.data) return; renderMap(); renderRoutes(); renderDetails(); }

$('#route-form').addEventListener('submit', event => { event.preventDefault(); calculate({ preserveSelection: false }); });
$$('[data-mode]').forEach(button => button.addEventListener('click', () => { state.mode = button.dataset.mode; $$('[data-mode]').forEach(item => item.classList.toggle('active', item === button)); const simulated = state.mode === 'simulated'; $$('.control-row input').forEach(input => input.disabled = !simulated); calculate(); }));
$$('[data-heatmap]').forEach(button => button.addEventListener('click', () => { state.heatmap = button.dataset.heatmap; $$('[data-heatmap]').forEach(item => item.classList.toggle('active', item === button)); calculate(); }));
$$('.control-row input').forEach(input => input.addEventListener('input', () => { updateControlOutputs(); clearTimeout(state.timer); state.timer = setTimeout(() => calculate(), 180); }));
$('#reset-controls').addEventListener('click', () => { $('#hour').value = 17; $('#weather').value = 1; $('#congestion').value = 56; $('#demand').value = 68; updateControlOutputs(); calculate(); });
$('#reset-view').addEventListener('click', () => { state.selectedRouteId = state.data?.recommended_route_id; render(); });
$('#location-button').addEventListener('click', () => { if (!navigator.geolocation) return showToast('GPS is unavailable. Enter a starting point manually.'); navigator.geolocation.getCurrentPosition(() => { $('#origin').value = 'Current location'; calculate({ preserveSelection: false }); }, () => showToast('Location permission was denied. Enter a starting point manually.')); });
window.addEventListener('offline', () => showToast('Internet connection lost. The loaded simulation remains available.'));
updateControlOutputs(); calculate({ preserveSelection: false });
