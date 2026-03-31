import json

import pytest

from utils.sql_chat import parse_sql_from_model_text


def test_parse_sql_from_json_object():
    text = json.dumps({"sql": "SELECT COUNT(*) FROM t"})
    assert parse_sql_from_model_text(text) == "SELECT COUNT(*) FROM t"


def test_parse_sql_from_fence():
    text = 'Here is the query:\n```sql\nSELECT 1\n```'
    assert parse_sql_from_model_text(text) == "SELECT 1"


def test_parse_raw_select():
    assert parse_sql_from_model_text("SELECT 1 AS x") == "SELECT 1 AS x"


def test_parse_invalid_raises():
    with pytest.raises(ValueError):
        parse_sql_from_model_text("not sql here")
