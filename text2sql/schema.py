"""
RAGTUNE Enterprise Text-to-SQL Engine - Schema Intelligence & Introspector
Manages database metadata, table schemas, column data types, relationships, and business term mappings.
"""

import threading
from typing import Dict, List, Optional
from text2sql.domain import TableSchema, ColumnSchema


class SchemaIntrospector:
    def __init__(self):
        self._lock = threading.RLock()
        self._schemas: Dict[str, TableSchema] = {}
        self._seed_default_enterprise_schemas()

    def _seed_default_enterprise_schemas(self):
        """Seeds standard enterprise analytics database schemas."""
        sales_table = TableSchema(
            table_name="sales",
            description="Enterprise quarterly sales transactions and regional revenue records",
            tenant_id="org_acme",
            columns=[
                ColumnSchema(name="id", data_type="INTEGER", is_primary_key=True),
                ColumnSchema(name="region", data_type="VARCHAR(50)", description="Geographic sales region"),
                ColumnSchema(name="quarter", data_type="VARCHAR(10)", description="Fiscal quarter (e.g. Q1, Q2, Q3, Q4)"),
                ColumnSchema(name="revenue", data_type="DECIMAL(12,2)", description="Total revenue generated in USD"),
                ColumnSchema(name="units_sold", data_type="INTEGER", description="Total software license units sold"),
                ColumnSchema(name="created_at", data_type="TIMESTAMP", description="Record creation timestamp"),
            ]
        )
        employees_table = TableSchema(
            table_name="employees",
            description="Enterprise employee directory and organizational department records",
            tenant_id="org_acme",
            columns=[
                ColumnSchema(name="employee_id", data_type="VARCHAR(20)", is_primary_key=True),
                ColumnSchema(name="full_name", data_type="VARCHAR(100)", description="Employee full name"),
                ColumnSchema(name="department", data_type="VARCHAR(50)", description="Department name"),
                ColumnSchema(name="role", data_type="VARCHAR(50)", description="Job title or security role"),
                ColumnSchema(name="salary", data_type="DECIMAL(12,2)", description="Confidential base annual salary"),
            ]
        )
        self.register_table(sales_table)
        self.register_table(employees_table)

    def register_table(self, schema: TableSchema):
        with self._lock:
            self._schemas[schema.table_name] = schema

    def get_table(self, table_name: str) -> Optional[TableSchema]:
        with self._lock:
            return self._schemas.get(table_name)

    def list_tables(self, tenant_id: Optional[str] = None) -> List[TableSchema]:
        with self._lock:
            tables = list(self._schemas.values())
            if tenant_id:
                tables = [t for t in tables if t.tenant_id in [tenant_id, "global_tenant"]]
            return tables

    def match_tables_for_query(self, query: str) -> List[TableSchema]:
        """Matches relevant database tables based on query business terminology."""
        q_lower = query.lower()
        matched = []
        with self._lock:
            for t in self._schemas.values():
                if t.table_name.lower() in q_lower or any(c.name.lower() in q_lower for c in t.columns):
                    matched.append(t)
                elif "sales" in q_lower or "revenue" in q_lower:
                    if t.table_name == "sales":
                        matched.append(t)
            if not matched and self._schemas:
                matched.append(list(self._schemas.values())[0])
            return matched
