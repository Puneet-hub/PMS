"""
Populate the database with demo data so the app can be evaluated
without manually clicking through the UI first.

Run with:  python -m app.seed
"""

from datetime import date, timedelta

from app.database import SessionLocal
from app.security import hash_password
from app.models import (
    User,
    UserRole,
    Property,
    Unit,
    UnitStatus,
    Lease,
    LeaseStatus,
    Payment,
    PaymentStatus,
    MaintenanceRequest,
    MaintenancePriority,
    MaintenanceStatus,
    MaintenanceComment,
)

DEMO_PASSWORD = "Password123!"


def run():
    db = SessionLocal()

    try:
        if db.query(User).first():
            print("Database already has data -- skipping seed. "
                  "Drop and re-migrate the DB if you want a clean seed.")
            return

        # --- Users ---------------------------------------------------
        admin = User(
            name="Alice Admin",
            email="admin@demo.com",
            role=UserRole.ADMIN,
            password_hash=hash_password(DEMO_PASSWORD),
        )
        manager = User(
            name="Mike Manager",
            email="manager@demo.com",
            role=UserRole.PROPERTY_MANAGER,
            password_hash=hash_password(DEMO_PASSWORD),
        )
        manager2 = User(
            name="Priya Manager",
            email="manager2@demo.com",
            role=UserRole.PROPERTY_MANAGER,
            password_hash=hash_password(DEMO_PASSWORD),
        )
        tenant1 = User(
            name="Tom Tenant",
            email="tenant@demo.com",
            role=UserRole.TENANT,
            password_hash=hash_password(DEMO_PASSWORD),
        )
        tenant2 = User(
            name="Tara Tenant",
            email="tenant2@demo.com",
            role=UserRole.TENANT,
            password_hash=hash_password(DEMO_PASSWORD),
        )
        db.add_all([admin, manager, manager2, tenant1, tenant2])
        db.commit()

        # --- Properties & Units ---------------------------------------
        prop1 = Property(title="Sunrise Apartments", address="12 Sunrise Ave, Pune", manager_id=manager.id)
        prop2 = Property(title="Maple Residency", address="88 Maple St, Pune", manager_id=manager.id)
        prop3 = Property(title="Lakeview Towers", address="5 Lakeview Rd, Pune", manager_id=manager2.id)
        db.add_all([prop1, prop2, prop3])
        db.commit()

        unit1 = Unit(property_id=prop1.id, unit_number="101", bedrooms=2, bathrooms=1,
                     monthly_rent=25000, status=UnitStatus.OCCUPIED)
        unit2 = Unit(property_id=prop1.id, unit_number="102", bedrooms=1, bathrooms=1,
                     monthly_rent=18000, status=UnitStatus.AVAILABLE)
        unit3 = Unit(property_id=prop2.id, unit_number="A1", bedrooms=3, bathrooms=2,
                     monthly_rent=35000, status=UnitStatus.OCCUPIED)
        unit4 = Unit(property_id=prop2.id, unit_number="A2", bedrooms=2, bathrooms=2,
                     monthly_rent=28000, status=UnitStatus.MAINTENANCE)
        unit5 = Unit(property_id=prop3.id, unit_number="201", bedrooms=1, bathrooms=1,
                     monthly_rent=20000, status=UnitStatus.AVAILABLE)
        db.add_all([unit1, unit2, unit3, unit4, unit5])
        db.commit()

        # --- Leases -----------------------------------------------------
        lease1 = Lease(
            tenant_id=tenant1.id, unit_id=unit1.id,
            start_date=date.today() - timedelta(days=200),
            end_date=date.today() + timedelta(days=165),
            monthly_rent=25000, security_deposit=50000,
            status=LeaseStatus.ACTIVE,
        )
        lease2 = Lease(
            tenant_id=tenant2.id, unit_id=unit3.id,
            start_date=date.today() - timedelta(days=90),
            end_date=date.today() + timedelta(days=275),
            monthly_rent=35000, security_deposit=70000,
            status=LeaseStatus.ACTIVE,
        )
        db.add_all([lease1, lease2])
        db.commit()

        # --- Payments -----------------------------------------------------
        db.add_all([
            Payment(lease_id=lease1.id, amount=25000,
                    due_date=date.today().replace(day=1) - timedelta(days=60),
                    paid_date=date.today() - timedelta(days=58), status=PaymentStatus.PAID),
            Payment(lease_id=lease1.id, amount=25000,
                    due_date=date.today().replace(day=1) - timedelta(days=30),
                    paid_date=date.today() - timedelta(days=28), status=PaymentStatus.PAID),
            Payment(lease_id=lease1.id, amount=25000,
                    due_date=date.today() + timedelta(days=5), status=PaymentStatus.PENDING),
            Payment(lease_id=lease2.id, amount=35000,
                    due_date=date.today() - timedelta(days=10), status=PaymentStatus.LATE),
            Payment(lease_id=lease2.id, amount=35000,
                    due_date=date.today() + timedelta(days=20), status=PaymentStatus.PENDING),
        ])
        db.commit()

        # --- Maintenance requests -----------------------------------------
        req1 = MaintenanceRequest(
            unit_id=unit1.id, created_by_id=tenant1.id, assigned_manager_id=manager.id,
            title="Leaking kitchen faucet",
            description="The kitchen faucet has been dripping constantly for two days.",
            priority=MaintenancePriority.MEDIUM, status=MaintenanceStatus.IN_PROGRESS,
        )
        req2 = MaintenanceRequest(
            unit_id=unit3.id, created_by_id=tenant2.id,
            title="AC not cooling",
            description="Living room AC unit runs but does not cool the room at all.",
            priority=MaintenancePriority.HIGH, status=MaintenanceStatus.OPEN,
        )
        db.add_all([req1, req2])
        db.commit()

        db.add(MaintenanceComment(
            maintenance_request_id=req1.id, author_id=manager.id,
            content="Plumber scheduled for tomorrow morning.",
        ))
        db.commit()

        print("Seed data created.")
        print("Demo credentials (password for all: 'Password123!'):")
        print("  admin@demo.com        (ADMIN)")
        print("  manager@demo.com      (PROPERTY_MANAGER, owns Sunrise + Maple)")
        print("  manager2@demo.com     (PROPERTY_MANAGER, owns Lakeview)")
        print("  tenant@demo.com       (TENANT, leases Sunrise 101)")
        print("  tenant2@demo.com      (TENANT, leases Maple A1)")

    finally:
        db.close()


if __name__ == "__main__":
    run()
