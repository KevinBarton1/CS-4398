import json

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class ApiResponseLoggerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        if not request.url.path.startswith("/api/"):
            return response

        body = b""
        async for chunk in response.body_iterator:
            body += chunk

        print(f"\n--- {request.method} {request.url.path} -> {response.status_code} ---")
        try:
            print(json.dumps(json.loads(body.decode()), indent=2))
        except (json.JSONDecodeError, UnicodeDecodeError):
            print(body.decode(errors="replace"))
        print("--- end ---\n")

        return Response(
            content=body,
            status_code=response.status_code,
            headers=dict(response.headers),
            media_type=response.media_type,
        )
