"""
RAGTUNE - Test Suite for Text-to-SQL Engine
"""

import pytest
from sqlalchemy import text
from storage.db_connector import DBConnector
from text2sql.engine import Text2SQLEngine


def test_text2sql_generation_and_execution():
    db = DBConnector("sqlite:///:memory:")
    # Seed temp table
    with db.engine.connect() as conn:
        conn.execute(text("CREATE TABLE sales (id INT, amount REAL);"))
        conn.execute(text("INSERT INTO sales VALUES (1, 500.0), (2, 750.0);"))
        conn.commit()

    engine = Text2SQLEngine(db)
    res = engine.process_query("What is the total sales amount?")

    assert res.success
    assert "sales" in res.sanitized_sql.lower()
    assert len(res.rows) > 0
