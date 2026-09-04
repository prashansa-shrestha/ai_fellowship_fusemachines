# Force IPv4. This network drops IPv6 quietly, so clients that prefer AAAA
# hang instead of failing over. Patch DNS for requests/urllib3, and bind
# httpx to 0.0.0.0 for the Gemini SDK.
import socket

import httpx

_getaddrinfo = socket.getaddrinfo


def force_ipv4_dns() -> None:
    def ipv4_only(host, port, family=0, type=0, proto=0, flags=0):
        return _getaddrinfo(host, port, socket.AF_INET, type, proto, flags)

    socket.getaddrinfo = ipv4_only


def ipv4_httpx_client() -> httpx.Client:
    return httpx.Client(transport=httpx.HTTPTransport(local_address="0.0.0.0"))
