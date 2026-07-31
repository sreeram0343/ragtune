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
        conn.execute(text("CREATE TABLE sales (id INT, region TEXT, revenue REAL);"))
        conn.execute(text("INSERT INTO sales VALUES (1, 'NORTH_AMERICA', 500.0), (2, 'EUROPE', 750.0);"))
        conn.commit()

    engine = Text2SQLEngine(db)
    res = engine.process_query("What is the total sales amount?")

    assert res.success
    assert "sales" in res.sanitized_sql.lower()
    assert len(res.rows) > 0


def test_text2sql_dynamic_filtering():
    engine = Text2SQLEngine(db_path="demo_data/enterprise_db.sqlite")
    res = engine.process_query("Show total revenue for NORTH_AMERICA")
    assert res.success
    assert "north_america" in res.sanitized_sql.lower() or "region" in res.sanitized_sql.lower()


def test_text2sql_employee_salary_sorting():
    engine = Text2SQLEngine(db_path="demo_data/enterprise_db.sqlite")
    res = engine.process_query("Who are the highest paid employees?")
    assert res.success
    assert "employees" in res.sanitized_sql.lower()
    assert "order by" in res.sanitized_sql.lower()

