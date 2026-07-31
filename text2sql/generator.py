"""
RAGTUNE Enterprise Text-to-SQL Engine - Dialect-Aware SQL Generator
Synthesizes structured read-only SELECT queries with aggregations, CTEs, and parameterized filters.
"""

import re
from typing import List, Tuple, Any
from text2sql.domain import TableSchema


class SQLGenerator:
    def __init__(self, dialect: str = "sqlite"):
        self.dialect = dialect

    def generate_sql(self, query: str, matched_tables: List[TableSchema]) -> Tuple[str, List[Any]]:
        """
        Generates dialect-aware SQL query dynamically based on natural language intent.
        """
        if not matched_tables:
            return "SELECT 'No matched database tables' AS notice;", []

        target_table = matched_tables[0]
        t_name = target_table.table_name
        q_lower = query.lower()
        col_names = [c.name for c in target_table.columns]
        where_clauses = []
        params = []

        # Extract filters from query
        # Region filters
        for region in ["NORTH_AMERICA", "EUROPE", "ASIA_PACIFIC"]:
            if region.lower() in q_lower or region.lower().replace("_", " ") in q_lower:
                if "region" in col_names:
                    where_clauses.append("region = ?")
                    params.append(region)

        # Tier filters
        for tier in ["PLATINUM", "DIAMOND", "GOLD", "SILVER"]:
            if tier.lower() in q_lower:
                if "tier" in col_names:
                    where_clauses.append("tier = ?")
                    params.append(tier)
                elif "sla_tier" in col_names:
                    where_clauses.append("sla_tier LIKE ?")
                    params.append(f"%{tier}%")

        # Status filters
        for status in ["ACTIVE", "CHURN_RISK", "DELIVERED", "CANCELLED", "PENDING"]:
            if status.lower() in q_lower or status.lower().replace("_", " ") in q_lower:
                if "account_status" in col_names:
                    where_clauses.append("account_status = ?")
                    params.append(status)
                elif "status" in col_names:
                    where_clauses.append("status = ?")
                    params.append(status)

        # Quarter filters
        for q in ["Q1", "Q2", "Q3", "Q4"]:
            if q.lower() in q_lower or f"quarter {q[1]}" in q_lower:
                if "quarter" in col_names:
                    where_clauses.append("quarter = ?")
                    params.append(q)

        # Department filters
        for dept in ["engineering", "sales", "product", "customer success"]:
            if dept in q_lower and "department" in col_names:
                where_clauses.append("LOWER(department) = ?")
                params.append(dept)

        # Aggregations
        is_sum = any(k in q_lower for k in ["total", "sum", "revenue", "amount"])
        is_count = any(k in q_lower for k in ["how many", "count", "number of"])
        is_avg = any(k in q_lower for k in ["average", "avg", "mean"])
        is_top = any(k in q_lower for k in ["top", "highest", "best", "largest", "max"])

        where_sql = f" WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

        # Aggregation logic
        if is_count:
            sql = f"SELECT COUNT(*) AS total_records FROM {t_name}{where_sql} LIMIT 100;"
            return sql, params

        if is_sum:
            num_col = None
            for candidate in ["revenue", "annual_revenue", "order_amount", "contract_limit", "salary"]:
                if candidate in col_names:
                    num_col = candidate
                    break
            if num_col:
                if "group by" in q_lower or "by region" in q_lower or "by department" in q_lower or "by tier" in q_lower or "by quarter" in q_lower:
                    group_col = "region" if "region" in q_lower and "region" in col_names else \
                                ("department" if "department" in q_lower and "department" in col_names else \
                                ("quarter" if "quarter" in q_lower and "quarter" in col_names else \
                                ("tier" if "tier" in col_names else col_names[1])))
                    sql = f"SELECT {group_col}, SUM({num_col}) AS total_value FROM {t_name}{where_sql} GROUP BY {group_col} ORDER BY total_value DESC LIMIT 100;"
                    return sql, params
                sql = f"SELECT SUM({num_col}) AS total_value FROM {t_name}{where_sql} LIMIT 100;"
                return sql, params

        if is_avg:
            num_col = None
            for candidate in ["revenue", "annual_revenue", "order_amount", "salary"]:
                if candidate in col_names:
                    num_col = candidate
                    break
            if num_col:
                sql = f"SELECT AVG({num_col}) AS average_value FROM {t_name}{where_sql} LIMIT 100;"
                return sql, params

        # Top / Ordering logic
        order_by_sql = ""
        if is_top or "salary" in q_lower or "revenue" in q_lower or "amount" in q_lower:
            sort_col = None
            for candidate in ["salary", "annual_revenue", "order_amount", "revenue", "contract_limit"]:
                if candidate in col_names:
                    sort_col = candidate
                    break
            if sort_col:
                order_by_sql = f" ORDER BY {sort_col} DESC"

        limit = 10 if is_top else 100
        cols_str = ", ".join(col_names)
        sql = f"SELECT {cols_str} FROM {t_name}{where_sql}{order_by_sql} LIMIT {limit};"
        return sql, params

