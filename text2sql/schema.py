"""
RAGTUNE Enterprise Text-to-SQL Engine - Schema Intelligence & Introspector
Manages database metadata, table schemas, column data types, relationships, and business term mappings.
"""

import os
import sqlite3
import threading

from text2sql.domain import ColumnSchema, TableSchema


class SchemaIntrospector:
    def __init__(self, db_path: str = "demo_data/enterprise_db.sqlite"):
        self._lock = threading.RLock()
        self._schemas: dict[str, TableSchema] = {}
        self.db_path = db_path
        self._seed_default_enterprise_schemas()
        self.introspect_sqlite_db(self.db_path)

    def _seed_default_enterprise_schemas(self):
        """Seeds standard enterprise analytics database schemas."""
        sales_table = TableSchema(
            table_name="sales",
            description="Enterprise quarterly sales transactions and regional revenue records",
            tenant_id="org_acme",
            columns=[
                ColumnSchema(name="id", data_type="INTEGER", is_primary_key=True),
                ColumnSchema(
                    name="region",
                    data_type="VARCHAR(50)",
                    description="Geographic sales region",
                ),
                ColumnSchema(
                    name="quarter",
                    data_type="VARCHAR(10)",
                    description="Fiscal quarter (e.g. Q1, Q2, Q3, Q4)",
                ),
                ColumnSchema(
                    name="revenue",
                    data_type="DECIMAL(12,2)",
                    description="Total revenue generated in USD",
                ),
                ColumnSchema(
                    name="units_sold",
                    data_type="INTEGER",
                    description="Total software license units sold",
                ),
                ColumnSchema(
                    name="created_at",
                    data_type="TIMESTAMP",
                    description="Record creation timestamp",
                ),
            ],
        )
        employees_table = TableSchema(
            table_name="employees",
            description="Enterprise employee directory and organizational department records",
            tenant_id="org_acme",
            columns=[
                ColumnSchema(
                    name="employee_id", data_type="VARCHAR(20)", is_primary_key=True
                ),
                ColumnSchema(
                    name="full_name",
                    data_type="VARCHAR(100)",
                    description="Employee full name",
                ),
                ColumnSchema(
                    name="department",
                    data_type="VARCHAR(50)",
                    description="Department name",
                ),
                ColumnSchema(
                    name="role",
                    data_type="VARCHAR(50)",
                    description="Job title or security role",
                ),
                ColumnSchema(
                    name="salary",
                    data_type="DECIMAL(12,2)",
                    description="Confidential base annual salary",
                ),
            ],
        )
        customers_table = TableSchema(
            table_name="customers",
            description="Enterprise customer accounts, tiers, revenue, and status",
            tenant_id="org_acme",
            columns=[
                ColumnSchema(name="customer_id", data_type="TEXT", is_primary_key=True),
                ColumnSchema(
                    name="company_name", data_type="TEXT", description="Company name"
                ),
                ColumnSchema(
                    name="tier",
                    data_type="TEXT",
                    description="Service tier (PLATINUM, DIAMOND, GOLD, SILVER)",
                ),
                ColumnSchema(
                    name="annual_revenue",
                    data_type="REAL",
                    description="Annual revenue in USD",
                ),
                ColumnSchema(
                    name="account_status",
                    data_type="TEXT",
                    description="Account status (ACTIVE, CHURN_RISK)",
                ),
                ColumnSchema(
                    name="region", data_type="TEXT", description="Geographic region"
                ),
            ],
        )
        orders_table = TableSchema(
            table_name="orders",
            description="Enterprise customer transaction orders and status",
            tenant_id="org_acme",
            columns=[
                ColumnSchema(name="order_id", data_type="TEXT", is_primary_key=True),
                ColumnSchema(
                    name="customer_id",
                    data_type="TEXT",
                    description="Foreign key to customer_id",
                ),
                ColumnSchema(
                    name="order_date",
                    data_type="TEXT",
                    description="Order placement date",
                ),
                ColumnSchema(
                    name="order_amount",
                    data_type="REAL",
                    description="Order value amount in USD",
                ),
                ColumnSchema(
                    name="status",
                    data_type="TEXT",
                    description="Order status (DELIVERED, CANCELLED, PENDING)",
                ),
            ],
        )
        contracts_table = TableSchema(
            table_name="contracts",
            description="Enterprise SLA contracts and terms",
            tenant_id="org_acme",
            columns=[
                ColumnSchema(name="contract_id", data_type="TEXT", is_primary_key=True),
                ColumnSchema(
                    name="customer_id",
                    data_type="TEXT",
                    description="Foreign key to customer_id",
                ),
                ColumnSchema(
                    name="sla_tier", data_type="TEXT", description="SLA tier name"
                ),
                ColumnSchema(
                    name="contract_limit",
                    data_type="REAL",
                    description="Contract value limit",
                ),
                ColumnSchema(
                    name="start_date",
                    data_type="TEXT",
                    description="Contract start date",
                ),
                ColumnSchema(
                    name="end_date", data_type="TEXT", description="Contract end date"
                ),
            ],
        )
        self.register_table(sales_table)
        self.register_table(employees_table)
        self.register_table(customers_table)
        self.register_table(orders_table)
        self.register_table(contracts_table)

    def introspect_sqlite_db(self, db_path: str):
        """Introspects SQLite database tables and updates schema registry dynamically."""
        if not os.path.exists(db_path):
            return
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [
                row[0] for row in cursor.fetchall() if not row[0].startswith("sqlite_")
            ]
            for t_name in tables:
                cursor.execute(f"PRAGMA table_info({t_name});")
                cols = cursor.fetchall()
                col_schemas = [
                    ColumnSchema(
                        name=col[1],
                        data_type=col[2] or "TEXT",
                        is_primary_key=bool(col[5]),
                    )
                    for col in cols
                ]
                t_schema = TableSchema(
                    table_name=t_name,
                    description=f"Enterprise {t_name} table",
                    tenant_id="org_acme",
                    columns=col_schemas,
                )
                self.register_table(t_schema)
            conn.close()
        except Exception:
            pass

    def register_table(self, schema: TableSchema):
        with self._lock:
            self._schemas[schema.table_name] = schema

    def get_table(self, table_name: str) -> TableSchema | None:
        with self._lock:
            return self._schemas.get(table_name)

    def list_tables(self, tenant_id: str | None = None) -> list[TableSchema]:
        with self._lock:
            tables = list(self._schemas.values())
            if tenant_id:
                tables = [
                    t for t in tables if t.tenant_id in [tenant_id, "global_tenant"]
                ]
            return tables

    def match_tables_for_query(self, query: str) -> list[TableSchema]:
        """Matches relevant database tables based on query business terminology using exact word boundaries."""
        import re

        q_lower = query.lower()
        matched = []
        with self._lock:
            for t in self._schemas.values():
                t_name = t.table_name.lower()
                # Check exact table name or column name as word boundary
                t_match = bool(re.search(r"\b" + re.escape(t_name) + r"\b", q_lower))
                c_match = any(
                    len(c.name) > 2
                    and bool(
                        re.search(r"\b" + re.escape(c.name.lower()) + r"\b", q_lower)
                    )
                    for c in t.columns
                )
                if t_match or c_match or (
                    "customer" in q_lower or "client" in q_lower or "tier" in q_lower
                ) and t_name == "customers" or (
                    "order" in q_lower
                    or "transaction" in q_lower
                    or "purchase" in q_lower
                ) and t_name == "orders" or (
                    "contract" in q_lower or "sla" in q_lower or "agreement" in q_lower
                ) and t_name == "contracts" or ("sales" in q_lower or "revenue" in q_lower) and t_name in [
                    "sales",
                    "customers",
                    "orders",
                ] or (
                    "employee" in q_lower
                    or "employees" in q_lower
                    or "staff" in q_lower
                    or "salary" in q_lower
                    or "paid" in q_lower
                    or "department" in q_lower
                ) and t_name == "employees":
                    matched.append(t)

            # Deduplicate matched while preserving order
            unique_matched = []
            seen = set()
            for m in matched:
                if m.table_name not in seen:
                    seen.add(m.table_name)
                    unique_matched.append(m)

            if not unique_matched and self._schemas:
                unique_matched.append(list(self._schemas.values())[0])
            return unique_matched
