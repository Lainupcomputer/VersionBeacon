import pytest

from lucs_uvc import InvalidVersionError, parse_version


def test_three_and_four_part_versions_compare_correctly():
    assert parse_version("1.2.3") == parse_version("1.2.3.0")
    assert parse_version("1.2.4") > parse_version("1.2.3.9")
    assert parse_version("2.0.0") > parse_version("1.99.99.99")


@pytest.mark.parametrize("value", ["1", "1.2", "1.2.3.4.5", "1.2.x", ""])
def test_invalid_versions_are_rejected(value):
    with pytest.raises(InvalidVersionError):
        parse_version(value)
