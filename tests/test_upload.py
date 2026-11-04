import pytest

from core.upload import fetch_csv_url, parse_csv_bytes


def test_parse_csv_supports_latin1_and_delimiter_detection():
    frame, _ = parse_csv_bytes("name;value\nAndré;2\n".encode("latin-1"))
    assert frame.iloc[0]["name"] == "André"


@pytest.mark.parametrize("url", ["file:///tmp/data.csv", "http://127.0.0.1/data.csv", "https://user:pass@example.com/data.csv"])
def test_fetch_rejects_non_public_or_credential_urls(url):
    with pytest.raises(ValueError):
        fetch_csv_url(url)
