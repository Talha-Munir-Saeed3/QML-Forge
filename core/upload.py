"""Validated CSV ingestion for local files and public HTTP(S) URLs."""

import io
import importlib
import ipaddress
import socket
import os
import re
import csv
import zipfile
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener

import pandas as pd

from .config import MAX_UPLOAD_MB

KAGGLE_DATASET_PATTERN = re.compile(
    r"(?:https?://)?(?:www\.)?kaggle\.com/datasets/([^/?#]+)/([^/?#]+)",
    re.IGNORECASE,
)


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
        try:
            delimiter = csv.Sniffer().sniff(text[:8192], delimiters=",;\t|").delimiter
        except csv.Error:
            delimiter = ","
        return pd.read_csv(io.StringIO(text), sep=delimiter), raw
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


def kaggle_slug(url):
    match = KAGGLE_DATASET_PATTERN.fullmatch(url.strip().rstrip("/"))
    if not match:
        raise ValueError("Enter a Kaggle dataset URL such as https://www.kaggle.com/datasets/owner/dataset.")
    return f"{match.group(1)}/{match.group(2)}"


def _kaggle_api():
    if not os.getenv("KAGGLE_API_TOKEN") and not (
        os.getenv("KAGGLE_USERNAME") and os.getenv("KAGGLE_KEY")
    ):
        raise ValueError(
            "Kaggle credentials are not configured. Set KAGGLE_API_TOKEN or "
            "KAGGLE_USERNAME and KAGGLE_KEY in .env."
        )
    try:
        kaggle_module = importlib.import_module("kaggle.api.kaggle_api_extended")
        kaggle_api_class = kaggle_module.KaggleApi
    except (ImportError, AttributeError) as exc:
        raise ValueError("Install the Kaggle package with: pip install kaggle") from exc
    api = kaggle_api_class()
    try:
        api.authenticate()
    except Exception as exc:
        raise ValueError(f"Kaggle authentication failed: {exc}") from exc
    return api


def fetch_kaggle_archive(url):
    """Download a Kaggle dataset archive and return its bytes and CSV members."""
    import tempfile

    slug = kaggle_slug(url)
    with tempfile.TemporaryDirectory() as directory:
        api = _kaggle_api()
        try:
            api.dataset_download_files(slug, path=directory, unzip=False, quiet=True)
        except Exception as exc:
            raise ValueError(f"Kaggle download failed: {exc}") from exc
        archives = list(Path(directory).glob("*.zip"))
        if not archives:
            raise ValueError("Kaggle did not return a dataset archive.")
        archive_bytes = archives[0].read_bytes()
    with zipfile.ZipFile(io.BytesIO(archive_bytes)) as archive:
        csv_names = [name for name in archive.namelist()
                     if name.lower().endswith(".csv") and not name.endswith("/")]
    if not csv_names:
        raise ValueError("The Kaggle dataset does not contain a CSV file.")
    return archive_bytes, csv_names


def parse_kaggle_csv(archive_bytes, filename):
    with zipfile.ZipFile(io.BytesIO(archive_bytes)) as archive:
        try:
            info = archive.getinfo(filename)
        except KeyError as exc:
            raise ValueError("The selected Kaggle CSV is no longer available.") from exc
        if info.file_size > MAX_UPLOAD_MB * 1024 * 1024:
            raise ValueError(f"The selected Kaggle CSV exceeds the {MAX_UPLOAD_MB} MB limit.")
        raw = archive.read(filename)
    frame, raw = parse_csv_bytes(raw)
    return frame, raw, Path(filename).name


def fetch_kaggle_dataset(url, selected_file=None):
    """Download and parse one selected CSV from a Kaggle dataset."""
    archive_bytes, csv_names = fetch_kaggle_archive(url)
    if selected_file is None:
        if len(csv_names) != 1:
            raise ValueError("Select one CSV from the Kaggle dataset.")
        selected_file = csv_names[0]
    return parse_kaggle_csv(archive_bytes, selected_file)
