"""
RAGTUNE - Enterprise Seed Data Generator
Populates demo SQLite database and sample knowledge documents.
"""

import os
import sqlite3

def seed_enterprise_db(db_path: str = "demo_data/enterprise_db.sqlite"):
    os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 1. Customers Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS customers (
        customer_id TEXT PRIMARY KEY,
        company_name TEXT NOT NULL,
        tier TEXT NOT NULL,
        annual_revenue REAL,
        account_status TEXT,
        region TEXT
    );
    """)

    # 2. Orders Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        order_id TEXT PRIMARY KEY,
        customer_id TEXT,
        order_date TEXT,
        order_amount REAL,
        status TEXT,
        FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
    );
    """)

    # 3. Contracts Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS contracts (
        contract_id TEXT PRIMARY KEY,
        customer_id TEXT,
        sla_tier TEXT,
        contract_limit REAL,
        start_date TEXT,
        end_date TEXT,
        FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
    );
    """)

    # Seed Sample Customers
    cursor.execute("DELETE FROM customers;")
    customers = [
        ("CUST_101", "Acme Enterprise Solutions", "PLATINUM", 14500000.0, "ACTIVE", "NORTH_AMERICA"),
        ("CUST_102", "Nexus Global Health", "DIAMOND", 32000000.0, "ACTIVE", "EUROPE"),
        ("CUST_103", "Apex Logistics Corp", "GOLD", 8900000.0, "ACTIVE", "ASIA_PACIFIC"),
        ("CUST_104", "Starlight Media Group", "SILVER", 4200000.0, "CHURN_RISK", "NORTH_AMERICA"),
        ("CUST_105", "Vanguard Financial Technologies", "PLATINUM", 21500000.0, "ACTIVE", "NORTH_AMERICA"),
    ]
    cursor.executemany("INSERT INTO customers VALUES (?,?,?,?,?,?);", customers)

    # Seed Sample Orders
    cursor.execute("DELETE FROM orders;")
    orders = [
        ("ORD_9001", "CUST_101", "2024-01-15", 250000.0, "DELIVERED"),
        ("ORD_9002", "CUST_101", "2024-04-20", 310000.0, "DELIVERED"),
        ("ORD_9003", "CUST_102", "2024-02-10", 750000.0, "DELIVERED"),
        ("ORD_9004", "CUST_102", "2024-05-18", 820000.0, "DELIVERED"),
        ("ORD_9005", "CUST_103", "2024-03-01", 120000.0, "DELIVERED"),
        ("ORD_9006", "CUST_104", "2024-01-22", 45000.0, "CANCELLED"),
        ("ORD_9007", "CUST_105", "2024-06-12", 500000.0, "DELIVERED"),
    ]
    cursor.executemany("INSERT INTO orders VALUES (?,?,?,?,?);", orders)

    # Seed Sample Contracts
    cursor.execute("DELETE FROM contracts;")
    contracts = [
        ("CTR_501", "CUST_101", "PLATINUM_99_99", 500000.0, "2024-01-01", "2025-12-31"),
        ("CTR_502", "CUST_102", "DIAMOND_99_999", 1500000.0, "2024-01-01", "2026-12-31"),
        ("CTR_503", "CUST_103", "GOLD_99_9", 200000.0, "2024-03-01", "2025-02-28"),
        ("CTR_504", "CUST_105", "PLATINUM_99_99", 800000.0, "2024-06-01", "2026-05-31"),
    ]
    cursor.executemany("INSERT INTO contracts VALUES (?,?,?,?,?,?);", contracts)

    conn.commit()
    conn.close()


def seed_sample_documents(docs_dir: str = "demo_data/sample_documents"):
    os.makedirs(docs_dir, exist_ok=True)
    
    # Document 1: Enterprise SLA & Support Terms
    sla_path = os.path.join(docs_dir, "enterprise_sla_terms.md")
    with open(sla_path, "w", encoding="utf-8") as f:
        f.write("""# Enterprise Service Level Agreement (SLA) & Terms

## 1. Availability Commitments
RAGTUNE guarantees a 99.99% operational uptime for Platinum and Diamond enterprise tier customers.
For Gold tier customers, the guaranteed uptime commitment is 99.9%.

## 2. Response Time Metrics
- **Severity 1 (Critical Outage):** Initial response within 15 minutes. Resolution target within 2 hours.
- **Severity 2 (High Impact):** Initial response within 1 hour. Resolution target within 8 hours.
- **Severity 3 (Standard Request):** Initial response within 24 hours.

## 3. SLA Violation Credits
If uptime drops below the guaranteed threshold in any billing month, customer accounts receive a 15% SLA credit towards subsequent renewal invoicing.

## 4. Contract Limit Violations
If customer usage exceeds pre-agreed contract limits by more than 20% over two consecutive billing cycles, automatic audit inspection and HITL compliance review are triggered.
""")

    # Document 2: Expense & Travel Policy
    exp_path = os.path.join(docs_dir, "expense_reimbursement_policy.txt")
    with open(exp_path, "w", encoding="utf-8") as f:
        f.write("""ENTERPRISE EXPENSE REIMBURSEMENT POLICY

1. Overview
All enterprise employees must submit expense reports within 30 days of incurring costs.

2. Daily Per Diem Limits
- Domestic Travel Meal Per Diem: Up to $85 per day.
- International Travel Meal Per Diem: Up to $130 per day.
- Hotel Accommodation Capping: Standard room rates up to $300/night in major metropolitan centers.

3. Receipts & Proof of Payment
Itemized receipts are mandatory for any expense item exceeding $25.00. Alcohol expenses must be itemized separately and require Manager approval.

4. Approval Thresholds
- Expenses under $1,000 require Team Manager approval.
- Expenses between $1,000 and $5,000 require Department Director approval.
- Expenses exceeding $5,000 require Vice President approval and automated finance audit verification.
""")


if __name__ == "__main__":
    seed_enterprise_db()
    seed_sample_documents()
    print("Enterprise demo seed data generated successfully.")
