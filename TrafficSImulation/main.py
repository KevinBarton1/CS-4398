import json
import mimetypes
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from app.routes import plan_route


ROOT = Path(__file__).resolve().parent
STATIC = ROOT / "static"
PORT = 8000


class TrafficAppHandler(BaseHTTPRequestHandler):
    def _json(self, status, payload):
        encoded = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def do_POST(self):
        if urlparse(self.path).path != "/api/plan":
            self._json(404, {"error": "Not found"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length) or b"{}")
            self._json(200, plan_route(payload))
        except ValueError as error:
            self._json(400, {"error": str(error)})
        except Exception:
            self._json(500, {"error": "The route could not be calculated. Please retry."})

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/api/health":
            self._json(200, {"status": "ok", "service": "TrafficScope"})
            return
        relative = "index.html" if path == "/" else path.lstrip("/")
        file_path = (STATIC / relative).resolve()
        if STATIC.resolve() not in file_path.parents or not file_path.is_file():
            self.send_error(404)
            return
        content = file_path.read_bytes()
        content_type = mimetypes.guess_type(str(file_path))[0] or "application/octet-stream"
        self.send_response(200)
        self.send_header("Content-Type", f"{content_type}; charset=utf-8" if content_type.startswith("text/") else content_type)
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def log_message(self, format, *args):
        print(f"[TrafficScope] {format % args}")


def main():
    server = ThreadingHTTPServer(("127.0.0.1", PORT), TrafficAppHandler)
    print(f"TrafficScope is running at http://127.0.0.1:{PORT}")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
