const http = require('node:http');
const fs = require('node:fs');
const path = require('node:path');
const { planRoute } = require('./simulation');

const root = path.resolve(__dirname, '..');
const staticRoot = path.join(root, 'static');
const port = Number(process.env.PORT || 8000);
const types = { '.html': 'text/html; charset=utf-8', '.css': 'text/css; charset=utf-8', '.js': 'text/javascript; charset=utf-8', '.svg': 'image/svg+xml' };
const sendJson = (response, status, value) => { const body = JSON.stringify(value); response.writeHead(status, { 'Content-Type': 'application/json; charset=utf-8', 'Content-Length': Buffer.byteLength(body) }); response.end(body); };

const server = http.createServer((request, response) => {
  const url = new URL(request.url, `http://${request.headers.host || 'localhost'}`);
  if (request.method === 'GET' && url.pathname === '/api/health') return sendJson(response, 200, { status: 'ok', service: 'TrafficScope', runtime: 'node-fallback' });
  if (request.method === 'POST' && url.pathname === '/api/plan') {
    let body = '';
    request.on('data', chunk => { body += chunk; if (body.length > 100000) request.destroy(); });
    request.on('end', () => { try { sendJson(response, 200, planRoute(JSON.parse(body || '{}'))); } catch (error) { sendJson(response, 400, { error: error.message }); } });
    return;
  }
  if (request.method !== 'GET') return sendJson(response, 405, { error: 'Method not allowed' });
  const relative = url.pathname === '/' ? 'index.html' : url.pathname.replace(/^\/+/, '');
  const target = path.resolve(staticRoot, relative);
  if (!target.startsWith(staticRoot + path.sep) || !fs.existsSync(target) || !fs.statSync(target).isFile()) return sendJson(response, 404, { error: 'Not found' });
  const content = fs.readFileSync(target);
  response.writeHead(200, { 'Content-Type': types[path.extname(target)] || 'application/octet-stream', 'Content-Length': content.length });
  response.end(content);
});
server.listen(port, '127.0.0.1', () => console.log(`TrafficScope is running at http://127.0.0.1:${port}\nPress Ctrl+C to stop.`));
