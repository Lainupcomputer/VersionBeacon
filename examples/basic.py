"""Minimal VersionBeacon example using environment variables."""

from version_beacon import check


result = check()

if result.update_available:
    print(f"Update available: {result.latest_version}")
elif result.up_to_date:
    print("Application is up to date.")
elif result.current_is_ahead:
    print("Local version is newer than the version server.")
else:
    print(f"Version check failed: {result.error}")
