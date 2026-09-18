# LUCS-UVC

LUCS-UVC is a small Python library for checking whether an application is
running the latest available version.

The v2 API is designed to be simple for application developers:

```python
from lucs_uvc import check

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
python -m pip install lucs-uvc
```

## Environment variables

Configuration can be supplied through environment variables. Explicit
function arguments always take precedence over environment variables.

| Variable | Required | Default |
| --- | --- | --- |
| `LUCS_UVC_APP_NAME` | yes | — |
| `LUCS_UVC_CURRENT_VERSION` | yes | — |
| `LUCS_UVC_VERSION_URL` | yes | — |
| `LUCS_UVC_TIMEOUT` | no | `5` seconds |
| `LUCS_UVC_RETRIES` | no | `0` |
| `LUCS_UVC_MAX_RESPONSE_BYTES` | no | `1048576` |
| `LUCS_UVC_USER_AGENT` | no | `lucs-uvc/2` |

Then a check only needs:

```python
from lucs_uvc import check

result = check()
```

The environment prefix can be changed with `env_prefix` or by using
`UVCConfig.from_env(prefix="MY_APP_UVC_")`.

## Events

For repeated checks, use `VersionChecker` and register callbacks:

```python
from lucs_uvc import EventName, VersionChecker

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
