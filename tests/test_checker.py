import json

from lucs_uvc import (
    CheckStatus,
    EventName,
    UVCConfig,
    VersionChecker,
    check,
)


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def read(self, size=-1):
        if size >= 0:
            return self.payload[:size]
        return self.payload


def fake_urlopen(payload):
    def _urlopen(request, timeout):
        return FakeResponse(payload)

    return _urlopen


def make_config():
    return UVCConfig(
        app_name="MyApp",
        current_version="1.2.3",
        version_url="https://example.test/version.json",
    )


def test_json_update_is_detected(monkeypatch):
    payload = json.dumps(
        {
            "app_name": "MyApp",
            "version": "1.2.4",
            "release_url": "https://example.test/release",
        }
    ).encode()
    monkeypatch.setattr(
        "lucs_uvc.client.urllib_request.urlopen",
        fake_urlopen(payload),
    )

    result = VersionChecker(config=make_config()).check()

    assert result.status is CheckStatus.UPDATE_AVAILABLE
    assert result.update_available is True
    assert result.latest_version == "1.2.4"
    assert result.release_url == "https://example.test/release"


def test_legacy_text_response_is_still_readable(monkeypatch):
    monkeypatch.setattr(
        "lucs_uvc.client.urllib_request.urlopen",
        fake_urlopen(b"MyApp_version==1.2.3"),
    )

    result = VersionChecker(config=make_config()).check()

    assert result.status is CheckStatus.UP_TO_DATE


def test_events_are_emitted(monkeypatch):
    monkeypatch.setattr(
        "lucs_uvc.client.urllib_request.urlopen",
        fake_urlopen(b'{"version":"1.2.4"}'),
    )
    events = []
    checker = VersionChecker(config=make_config())
    checker.on(EventName.CHECK_STARTED, lambda payload: events.append("started"))
    checker.on(EventName.UPDATE_AVAILABLE, lambda payload: events.append("update"))
    checker.on(EventName.CHECK_FINISHED, lambda payload: events.append("finished"))

    checker.check()

    assert events == ["started", "update", "finished"]


def test_top_level_wrapper_reads_environment(monkeypatch):
    monkeypatch.setenv("LUCS_UVC_APP_NAME", "MyApp")
    monkeypatch.setenv("LUCS_UVC_CURRENT_VERSION", "1.2.3")
    monkeypatch.setenv("LUCS_UVC_VERSION_URL", "https://example.test/version.json")
    monkeypatch.setattr(
        "lucs_uvc.client.urllib_request.urlopen",
        fake_urlopen(b'{"version":"1.2.3"}'),
    )

    result = check()

    assert result.up_to_date is True
