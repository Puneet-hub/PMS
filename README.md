# Property Management System

A full-stack app for a property management company to manage properties, units,
tenants, leases, payments, and maintenance requests — with role-based access
enforced on the backend.

## Overview

- **Backend**: FastAPI + SQLAlchemy + PostgreSQL + Alembic, JWT auth, Pytest
- **Frontend**: React + TypeScript + Vite + Tailwind CSS
- **Roles**: `ADMIN`, `PROPERTY_MANAGER`, `TENANT` — enforced in the API, not just the UI

## Running the app

### Option A — Docker Compose (recommended)

```bash
docker compose up --build
```

This starts Postgres, runs migrations, seeds demo data, and starts both the API
and the frontend dev server.

- Frontend: http://localhost:5173
- Backend API: http://localhost:8000 (interactive docs at `/docs`)

### Option B — running locally without Docker

**Backend**

```bash
cd backend
python -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env           # edit DATABASE_URL if needed
# requires a running local Postgres with a database named `pms`

alembic upgrade head
python -m app.seed             # optional, but recommended for a quick demo
uvicorn app.main:app --reload
```

**Frontend**

```bash
cd frontend
npm install
cp .env.example .env           # VITE_API_URL, defaults to http://localhost:8000
npm run dev
```

**Tests** (uses a separate `pms_test` database so it never touches your dev data)

```bash
cd backend
createdb pms_test              # or: psql -c "CREATE DATABASE pms_test;"
pytest -v
```

## Environment variables

| Variable | Where | Purpose |
|---|---|---|
| `DATABASE_URL` | backend | SQLAlchemy connection string, e.g. `postgresql+psycopg2://postgres:postgres@localhost:5432/pms` |
| `VITE_API_URL` | frontend | Base URL the frontend calls, e.g. `http://localhost:8000` |

## Demo credentials

Password for every seeded account: **`Password123!`**

| Email | Role |
|---|---|
| admin@demo.com | ADMIN |
| manager@demo.com | PROPERTY_MANAGER (owns Sunrise Apartments, Maple Residency) |
| manager2@demo.com | PROPERTY_MANAGER (owns Lakeview Towers) |
| tenant@demo.com | TENANT (leases Sunrise 101) |
| tenant2@demo.com | TENANT (leases Maple A1) |

## Architecture

```
backend/
  app/
    models.py          # SQLAlchemy models
    schemas.py          # Pydantic request/response models
    security.py          # JWT issuing/verification, password hashing, role dependency
    permissions.py        # ownership/access-control helpers shared by routers
    database.py           # engine/session setup
    seed.py                # demo data
    routers/                # one file per resource
      auth.py, properties.py, units.py, leases.py,
      payments.py, maintenance.py, dashboard.py
    services/
      leases.py            # lease-overlap business rule, isolated for testing
  alembic/                  # migrations
  tests/                    # pytest suite (see below)

frontend/
  src/
    api.ts                 # fetch wrapper (auth header, error handling)
    AuthContext.tsx         # current user/token, login/logout
    Layout.tsx               # role-aware sidebar nav
    pages/                    # one file per screen
    types.ts                  # TS types mirroring backend schemas
```

**Data model**: `User → Property → Unit → Lease → Payment`, plus
`MaintenanceRequest → MaintenanceComment`. A `Lease` belongs to a `Unit` (not
directly to a `Property`), since a property has many units and each unit has
its own lease/tenant/rent history.

## Key technical & business decisions

- **Lease overlap prevention** lives in `app/services/leases.py`, isolated from
  the router so it's independently unit-testable. It checks only `ACTIVE`
  leases on a unit — a `TERMINATED`/`EXPIRED` lease never blocks a new one,
  even if the date ranges overlap on paper. Open-ended leases (`end_date =
  null`) are treated as blocking any later start date.
- **Authorization is enforced server-side** via `require_role(...)` dependency
  injection and per-resource ownership checks in `permissions.py` — a Property
  Manager can only act on properties/units/leases/maintenance requests tied to
  properties they manage; a Tenant can only see their own lease, unit, payments,
  and maintenance requests. The frontend also hides irrelevant UI per role, but
  that's a UX nicety, not the security boundary.
- **Unit status** (`AVAILABLE` / `OCCUPIED` / `MAINTENANCE`) is kept in sync
  automatically when a lease is created, updated, or deleted — except a unit
  manually flagged `MAINTENANCE` is left alone, since that's a deliberate
  manager decision rather than something derived from lease state.
- **User creation** (`POST /users`) has two modes: if no users exist yet, it
  allows creating the first `ADMIN` account unauthenticated (otherwise there's
  no way to bootstrap the system). After that, it requires authentication, and
  a `PROPERTY_MANAGER` may only create `TENANT` accounts.
- **Maintenance request status flow**: only `ADMIN`/`PROPERTY_MANAGER` can
  change status or assign a request; a `CLOSED` request cannot be reopened.
  Tenants can view and comment but not change workflow state.
- **Money fields** are stored as integers (smallest currency unit is assumed
  to be whole rupees for this demo) to avoid floating-point rounding issues.

## Testing

28 Pytest tests covering:
- Login success/failure, token validation
- Role-based authorization (tenant blocked from admin/manager endpoints, PM
  scoped to only their own properties)
- Tenant data isolation (cannot view another tenant's lease or maintenance
  request/comments)
- Lease overlap prevention (rejected, accepted when non-overlapping, and
  terminated leases correctly excluded from the check)
- Invalid lease dates (end before start)
- Maintenance request creation (tenant must have an active lease on the unit)
- Maintenance status-change permissions and status-flow validation

Tests use a real Postgres test database (`pms_test`) with per-test transaction
rollback, so they're fully isolated and don't require mocking the ORM.

## Known limitations / things I'd add with more time

- No refresh tokens — JWTs are long-lived for demo simplicity.
- No file/photo uploads on maintenance requests.
- No production-grade frontend build served via Nginx in Docker Compose (it
  runs the Vite dev server for simplicity, since deployment isn't required).
- No rate limiting on login.
