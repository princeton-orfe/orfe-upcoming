from src.enrich import enrich_titles


def test_enrich_overwrite_behavior(monkeypatch):
    """Verify overwrite flag forces replacement of existing non-empty titles."""
    html1 = """
    <html><body><div class="event-subtitle">First Subtitle</div></body></html>
    """.strip()
    html2 = """
    <html><body><div class="event-subtitle">Second Subtitle</div></body></html>
    """.strip()

    class DummyResp:
        def __init__(self, text: str, status_code: int = 200):
            self.text = text
            self.status_code = status_code

        def raise_for_status(self):  # noqa: D401
            if not (200 <= self.status_code < 300):
                raise RuntimeError("http error")

    calls = {"count": 0}

    def fake_get(url, timeout=15, headers=None):  # noqa: ARG001
        calls["count"] += 1
        # Return different subtitle texts per call to ensure overwrite effect visible
        return DummyResp(html1 if calls["count"] == 1 else html2)

    monkeypatch.setattr("src.enrich.requests.get", fake_get)

    events = [{"guid": "g1", "urlRef": "https://example.org/event/1", "title": ""}]

    stats1 = enrich_titles(events, enable=True)  # initial populate
    assert stats1.updated == 1
    assert events[0]["title"] == "First Subtitle"

    stats2 = enrich_titles(events, enable=True)  # no overwrite, should skip
    assert stats2.updated == 0
    assert events[0]["title"] == "First Subtitle"

    stats3 = enrich_titles(events, enable=True, overwrite=True)  # force overwrite
    assert stats3.updated == 1
    assert events[0]["title"] == "Second Subtitle"
