"""Validated CSV ingestion for local files and public HTTP(S) URLs."""

import io
import ipaddress
import socket
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener

import pandas as pd

from .config import MAX_UPLOAD_MB


def parse_csv_bytes(raw):
    if len(raw) > MAX_UPLOAD_MB * 1024 * 1024:
        raise ValueError(f"CSV exceeds the {MAX_UPLOAD_MB} MB upload limit.")
    if not raw:
        raise ValueError("The uploaded CSV is empty.")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        text = raw.decode("latin-1")
    try:
        return pd.read_csv(io.StringIO(text), sep=None, engine="python"), raw
    except (pd.errors.ParserError, UnicodeError) as exc:
        raise ValueError("Could not parse the CSV; check its delimiter and encoding.") from exc


def _public_host(hostname):
    try:
        addresses = socket.getaddrinfo(hostname, None)
    except socket.gaierror as exc:
        raise ValueError("The URL host could not be resolved.") from exc
    for address in addresses:
        if ipaddress.ip_address(address[4][0]).is_private or ipaddress.ip_address(address[4][0]).is_loopback:
            raise ValueError("Only public URL hosts are allowed.")


class _PublicRedirectHandler(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, new_url):
        parsed = urlparse(new_url)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            raise ValueError("The CSV URL redirected to an invalid address.")
        _public_host(parsed.hostname)
        return super().redirect_request(req, fp, code, msg, headers, new_url)


def fetch_csv_url(url, timeout=20):
    parsed = urlparse(url.strip())
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("Enter a complete public HTTP(S) URL.")
    if parsed.username or parsed.password:
        raise ValueError("URLs containing usernames or passwords are not allowed.")
    _public_host(parsed.hostname)
    request = Request(url, headers={"User-Agent": "QML-Forge/1.0"})
    try:
        opener = build_opener(_PublicRedirectHandler)
        with opener.open(request, timeout=timeout) as response:
            content_length = response.headers.get("Content-Length")
            if content_length and int(content_length) > MAX_UPLOAD_MB * 1024 * 1024:
                raise ValueError(f"CSV exceeds the {MAX_UPLOAD_MB} MB upload limit.")
            raw = response.read(MAX_UPLOAD_MB * 1024 * 1024 + 1)
    except ValueError:
        raise
    except (OSError, TimeoutError) as exc:
        raise ValueError(f"Could not download the CSV URL: {exc}") from exc
    frame, raw = parse_csv_bytes(raw)
    filename = Path(parsed.path).name or "url_dataset.csv"
    if not filename.lower().endswith(".csv"):
        filename += ".csv"
    return frame, raw, filename
