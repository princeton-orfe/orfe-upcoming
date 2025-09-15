import json
from pathlib import Path

from src.enrich import enrich_titles


class DummyResp:
    def __init__(self, text: str, status_code: int = 200):
        self.text = text
        self.status_code = status_code

    def raise_for_status(self):
        if not (200 <= self.status_code < 300):
            raise RuntimeError("http error")


def test_enrich_titles(monkeypatch):
    html = """
    <html><body>
      <div class="event-subtitle">Optimization and Learning in Stochastic Systems</div>
    </body></html>
    """

    def fake_get(url, timeout=15, headers=None):  # noqa: ARG001, D401
        return DummyResp(html)

    monkeypatch.setattr("src.enrich.requests.get", fake_get)
    events = [
        {"guid": "1", "urlRef": "https://example.org/event/1", "title": "", "speaker": "A"},
        {"guid": "2", "urlRef": "https://example.org/event/2", "title": "Existing", "speaker": "B"},
    ]
    stats = enrich_titles(events, enable=True)
    assert stats.attempted == 2
    # Only first gets updated (second retains existing title)
    assert events[0]["title"].startswith("Optimization and Learning")
    assert events[1]["title"] == "Existing"