from src.enrich import enrich_raw_details


class DummyResp:
    def __init__(self, text: str, status_code: int = 200):
        self.text = text
        self.status_code = status_code

    def raise_for_status(self):
        if not (200 <= self.status_code < 300):
            raise RuntimeError("http error")


def test_enrich_raw_details_basic(monkeypatch):
    html = """
    <html><body>
      <div class="events-detail-main"><p>Hello <strong>World</strong></p></div>
    </body></html>
    """

    def fake_get(url, timeout=15, headers=None):  # noqa: ARG001, D401
        return DummyResp(html)

    monkeypatch.setattr("src.enrich.requests.get", fake_get)
    events = [
        {"guid": "1", "urlRef": "https://example.org/event/1"},
        {"guid": "2", "urlRef": "https://example.org/event/2", "rawEventDetails": "pre"},
    ]
    stats = enrich_raw_details(events, enable=True, overwrite=False)
    assert stats.attempted == 2
    assert stats.updated == 1
    assert "<strong>World</strong>" in events[0]["rawEventDetails"]
    # second should not be overwritten without overwrite flag
    assert events[1]["rawEventDetails"] == "pre"


def test_enrich_raw_details_overwrite(monkeypatch):
    html = """
    <html><body>
      <div class="event-details-main"><div>Alt Container</div></div>
    </body></html>
    """

    def fake_get(url, timeout=15, headers=None):  # noqa: ARG001, D401
        return DummyResp(html)

    monkeypatch.setattr("src.enrich.requests.get", fake_get)
    events = [
        {"guid": "1", "urlRef": "https://example.org/event/1", "rawEventDetails": "old"},
    ]
    stats = enrich_raw_details(events, enable=True, overwrite=True)
    assert stats.updated == 1
    assert "Alt Container" in events[0]["rawEventDetails"]
