# VersionBeacon

VersionBeacon is a small Python library for checking whether an application is
running the latest available version.

The v2 API is designed to be simple for application developers:

```python
from version_beacon import check

result = check(
    app_name="MyApp",
    current_version="1.2.3",
    version_url="https://example.com/myapp-version.json",
)

if result.update_available:
    print(f"A new version is available: {result.latest_version}")
```

## Installation

```bash
python -m pip install version-beacon
```

## Environment variables

Configuration can be supplied through environment variables. Explicit
function arguments always take precedence over environment variables.

| Variable | Required | Default |
| --- | --- | --- |
| `VERSION_BEACON_APP_NAME` | yes | — |
| `VERSION_BEACON_CURRENT_VERSION` | yes | — |
| `VERSION_BEACON_VERSION_URL` | yes | — |
| `VERSION_BEACON_TIMEOUT` | no | `5` seconds |
| `VERSION_BEACON_RETRIES` | no | `0` |
| `VERSION_BEACON_MAX_RESPONSE_BYTES` | no | `1048576` |
| `VERSION_BEACON_USER_AGENT` | no | `version-beacon/2` |

Then a check only needs:

```python
from version_beacon import check

result = check()
```

The environment prefix can be changed with `env_prefix` or by using
`VersionBeaconConfig.from_env(prefix="MY_APP_VERSION_BEACON_")`.

## Events

For repeated checks, use `VersionChecker` and register callbacks:

```python
from version_beacon import EventName, VersionChecker

checker = VersionChecker.from_env()

@checker.on(EventName.UPDATE_AVAILABLE)
def update_available(result):
    print("Update:", result.latest_version)

@checker.on(EventName.UP_TO_DATE)
def already_current(result):
    print("Application is current")

@checker.on(EventName.CHECK_FAILED)
def check_failed(result):
    print("Version check failed:", result.error)

result = checker.check()
```

Available events are:

- `check_started`
- `update_available`
- `up_to_date`
- `current_ahead`
- `check_failed`
- `check_finished`

Callback exceptions are logged and do not interrupt the version check.

## Version endpoint format

The recommended endpoint returns JSON:

```json
{
  "app_name": "MyApp",
  "version": "1.2.4",
  "release_url": "https://example.com/releases/1.2.4",
  "release_notes": "Bug fixes and improvements"
}
```

Versions may contain three or four numeric components, for example `1.2.3`
or `1.2.3.4`. `1.2.3` and `1.2.3.0` are treated as equal.

During migration, the previous text form is also accepted:

```text
MyApp_version==1.2.4
```

## Development

```bash
python -m pip install -e ".[dev]"
python -m pytest
python -m build
```

The project is released under the MIT license.
