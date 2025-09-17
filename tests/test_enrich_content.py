from src.enrich import enrich_content


class DummyResp:
    def __init__(self, text: str, status_code: int = 200):
        self.text = text
        self.status_code = status_code

    def raise_for_status(self):  # noqa: D401
        if not (200 <= self.status_code < 300):
            raise RuntimeError("http error")


def test_enrich_content_updates_when_empty(monkeypatch):
    html = """
    <html><body>
      <div class="event-description">This is the enriched body content.</div>
    </body></html>
    """.strip()

    def fake_get(url, timeout=15, headers=None):  # noqa: ARG001
        return DummyResp(html)

    monkeypatch.setattr("src.enrich.requests.get", fake_get)
    events = [
        {"guid": "1", "urlRef": "https://example.org/event/1", "content": ""},
        {"guid": "2", "urlRef": "https://example.org/event/2", "content": "Existing"},
    ]
    stats = enrich_content(events, enable=True, overwrite=False)
    assert stats.attempted == 2
    assert stats.updated == 1
    assert events[0]["content"] == "This is the enriched body content."
    assert events[1]["content"] == "Existing"


def test_enrich_content_overwrite(monkeypatch):
    html = """
    <html><body><div class="event-body">Overwritten body</div></body></html>
    """.strip()

    def fake_get(url, timeout=15, headers=None):  # noqa: ARG001
        return DummyResp(html)

    monkeypatch.setattr("src.enrich.requests.get", fake_get)
    events = [
        {"guid": "g1", "urlRef": "https://example.org/event/1", "content": "Keep?"}
    ]
    stats = enrich_content(events, enable=True, overwrite=True)
    assert stats.updated == 1
    assert events[0]["content"] == "Overwritten body"


def test_enrich_content_from_details_container_text(monkeypatch):
    html = (
        '<div class="events-detail-main">\n'
        '  <h2 class="details">Details</h2>\n'
        '  <div class="clearfix text-formatted field field--name-field-ps-body">\n'
        '    <div class="field__item"><div class="tex2jax_process">'
        '      <h3>Abstract</h3>'
        '      <p>We develop an SDF approach with N &gt;&gt; T.</p>'
        '      <h3>Short Bio</h3>'
        '      <p>Professor at HKUST.&nbsp;</p>'
        '    </div></div>\n'
        '  </div>\n'
        '</div>'
    )

    def fake_get(url, timeout=15, headers=None):  # noqa: ARG001
        return DummyResp(f"<html><body>{html}</body></html>")

    monkeypatch.setenv("ENRICH_CONTENT_FORMAT", "text")
    monkeypatch.setattr("src.enrich.requests.get", fake_get)
    events = [{"guid": "x", "urlRef": "https://ex.org/e/1", "content": ""}]
    stats = enrich_content(events, enable=True, overwrite=False)
    assert stats.updated == 1
    body = events[0]["content"]
    assert "Abstract" in body
    assert ">> T" in body  # HTML entities decoded
    assert "Short Bio" in body
    assert "HKUST" in body


def test_enrich_content_from_details_container_html(monkeypatch):
    html = (
        '<div class="event-details-main">\n'
        '  <h2 class="details">Details</h2>\n'
        '  <div class="field__item"><div class="tex2jax_process">'
        '    <h3>Abstract</h3><p>Line 1</p>'
        '  </div></div>\n'
        '</div>'
    )

    def fake_get(url, timeout=15, headers=None):  # noqa: ARG001
        return DummyResp(f"<html><body>{html}</body></html>")

    monkeypatch.setenv("ENRICH_CONTENT_FORMAT", "html")
    monkeypatch.setattr("src.enrich.requests.get", fake_get)
    events = [{"guid": "y", "urlRef": "https://ex.org/e/2", "content": ""}]
    stats = enrich_content(events, enable=True, overwrite=True)
    assert stats.updated == 1
    body = events[0]["content"]
    assert body.startswith("<h3>Abstract</h3>") or "<h3>Abstract</h3>" in body
    assert "<p>Line 1</p>" in body


def test_enrich_content_fallback_preserves_ics_when_parse_fails(monkeypatch):
    # No recognizable container; parsing yields empty body
    html = "<html><body><div class='something-else'>No details here</div></body></html>"

    def fake_get(url, timeout=15, headers=None):  # noqa: ARG001
        return DummyResp(html)

    # Case 1: existing ICS description present; overwrite=True should NOT blank it
    monkeypatch.setattr("src.enrich.requests.get", fake_get)
    events = [{"guid": "a", "urlRef": "https://ex.org/e/3", "content": "ICS description"}]
    stats = enrich_content(events, enable=True, overwrite=True)
    assert stats.updated == 0
    assert events[0]["content"] == "ICS description"

    # Case 2: existing is empty; result should remain empty (no accidental write)
    events2 = [{"guid": "b", "urlRef": "https://ex.org/e/4", "content": ""}]
    stats2 = enrich_content(events2, enable=True, overwrite=False)
    assert stats2.updated == 0
    assert events2[0]["content"] == ""
