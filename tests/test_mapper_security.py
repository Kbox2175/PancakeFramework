import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'framework'))

import pytest
from ovenware.mybatis.mapper import _validate_identifier


def test_valid_identifiers():
    assert _validate_identifier("users") == "users"
    assert _validate_identifier("user_table") == "user_table"
    assert _validate_identifier("_private") == "_private"
    assert _validate_identifier("Table123") == "Table123"


def test_sql_injection_rejected():
    with pytest.raises(ValueError):
        _validate_identifier("users; DROP TABLE users--")

    with pytest.raises(ValueError):
        _validate_identifier("users OR 1=1")

    with pytest.raises(ValueError):
        _validate_identifier("users`")

    with pytest.raises(ValueError):
        _validate_identifier('users"')

    with pytest.raises(ValueError):
        _validate_identifier("")


def test_column_injection_rejected():
    with pytest.raises(ValueError):
        _validate_identifier("name; DROP TABLE x", "column")

    with pytest.raises(ValueError):
        _validate_identifier("name OR 1=1", "column")
