class DomainError(Exception):
    code = "internal_error"
    status = 500

    def __init__(self, detail: str) -> None:
        self.detail = detail
        super().__init__(detail)


class InvalidLocationError(DomainError):
    code = "invalid_location"
    status = 400

    def __init__(self, query: str) -> None:
        super().__init__(
            f'Could not resolve "{query}" to an Austin-area location.'
        )


class NoRouteFoundError(DomainError):
    code = "no_route_found"
    status = 400

    def __init__(self) -> None:
        super().__init__("No drivable route was found between these locations.")


class MapsNotConfiguredError(DomainError):
    code = "maps_not_configured"
    status = 503

    def __init__(self) -> None:
        super().__init__("Google Maps is not configured on the server.")


class UpstreamUnavailableError(DomainError):
    code = "upstream_unavailable"
    status = 502

    def __init__(self, service: str) -> None:
        super().__init__(
            f"The Google {service} service returned an error. Try again shortly."
        )


class UpstreamTimeoutError(DomainError):
    code = "upstream_timeout"
    status = 504

    def __init__(self, service: str) -> None:
        super().__init__(
            f"The Google {service} service did not respond in time. "
            "Try again shortly."
        )


TrafficScopeError = DomainError
