# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with this repository.

## Project Overview

A RESTful Payment Reconciliation API built with Python/FastAPI and MySQL. It manages merchants, orders, and payments, then runs a matching algorithm to reconcile them.

## Development Commands

**Setup:**
```bash
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
python scripts/init_db.py  # initializes MySQL database and tables
```

**Run the server:**
```bash
uvicorn app.main:app --reload
```

**Explore the API:** Swagger UI is available at `http://localhost:8000/docs` after starting the server.

**Environment:** Copy `.env` and set `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`, `DB_NAME` for your MySQL instance.

> There is no automated test suite — manual testing is done via Swagger UI or cURL.

## Architecture

The app follows a 3-layer design:

```
FastAPI endpoints (app/main.py)
    ↓
SQLAlchemy ORM (app/models/db_schema.py)
    ↓
MySQL 8.0
```

**`app/main.py`** contains all route handlers and business logic, including the reconciliation algorithm.
**`app/models/db_schema.py`** defines the three SQLAlchemy ORM models: `Merchant`, `Order`, `Payment`.
**`app/schemas/`** contains Pydantic request/response models (one file per entity).
**`app/database.py`** sets up the SQLAlchemy engine and `get_db` dependency.
**`scripts/init_db.py`** creates all tables against the configured database.

## Key Domain Concepts

**Reconciliation algorithm** (`POST /reconciliation`) matches orders to payments using all of these criteria:
1. Same `merchant_order_id`
2. Same `merchant_id`
3. Exact amount match
4. Payment date within ±3 days of order date
5. Both records have `status = 'completed'`

When a match is found, both the order and payment are updated to `status = 'reconciled'`. Matching is one-to-one — processed records are skipped to prevent duplicate reconciliation.

**ID distinction:** `merchant_id` is a human-readable business identifier (e.g., `"MERCHANT_A"`), distinct from the auto-increment database primary key `id`.

## Data Model

- `merchants`: master data, identified by unique `merchant_id` string
- `orders`: expected transactions linked to a merchant via FK
- `payments`: actual processor transactions linked to a merchant via FK
- All tables use `Numeric(10,2)` for amounts and enum-based `status` fields (`pending`, `completed`, `failed`, `reconciled`)

## Tech Stack

| Component | Version |
|-----------|---------|
| Python | 3.13 |
| FastAPI | 0.128.0 |
| SQLAlchemy | 2.0.46 |
| Pydantic | 2.12.5 |
| Uvicorn | 0.30.0 |
| PyMySQL | 1.1.0 |
| MySQL | 8.0 |
