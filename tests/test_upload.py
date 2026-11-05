import pytest

import io
import zipfile

from core.upload import (fetch_csv_url, fetch_kaggle_dataset, kaggle_slug,
                         parse_csv_bytes, parse_kaggle_csv)


def test_parse_csv_supports_latin1_and_delimiter_detection():
    frame, _ = parse_csv_bytes("name;value\nAndré;2\n".encode("latin-1"))
    assert frame.iloc[0]["name"] == "André"


def test_kaggle_slug_is_extracted_from_dataset_page():
    assert kaggle_slug("https://www.kaggle.com/datasets/owner/sample-data") == "owner/sample-data"


def test_kaggle_requires_credentials(monkeypatch):
    monkeypatch.delenv("KAGGLE_API_TOKEN", raising=False)
    monkeypatch.delenv("KAGGLE_USERNAME", raising=False)
    monkeypatch.delenv("KAGGLE_KEY", raising=False)
    with pytest.raises(ValueError, match="Kaggle access"):
        fetch_kaggle_dataset("https://www.kaggle.com/datasets/owner/sample-data")


def test_selected_kaggle_csv_can_be_loaded_from_multi_file_archive():
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("features.csv", "x,y\n1,2\n")
        archive.writestr("labels.csv", "label\none\n")
    frame, _, filename = parse_kaggle_csv(buffer.getvalue(), "labels.csv")
    assert filename == "labels.csv"
    assert frame.iloc[0]["label"] == "one"


@pytest.mark.parametrize("url", ["file:///tmp/data.csv", "http://127.0.0.1/data.csv", "https://user:pass@example.com/data.csv"])
def test_fetch_rejects_non_public_or_credential_urls(url):
    with pytest.raises(ValueError):
        fetch_csv_url(url)
