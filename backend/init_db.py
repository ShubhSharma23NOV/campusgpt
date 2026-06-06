"""
Run once to create all tables and seed demo data.
Usage:  python init_db.py
"""
import asyncio
from datetime import date, datetime

from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import engine, AsyncSessionLocal
from app.core.security import hash_password

# Import all models so SQLAlchemy registers them
import app.models  # noqa: F401
from app.core.database import Base

from app.models.admin      import Admin
from app.models.student    import Student
from app.models.attendance import Subject, Attendance, AttendanceSummary
from app.models.fees       import Fee, FeePayment
from app.models.hostel     import Hostel, HostelAllocation
from app.models.scholarship import Scholarship, ScholarshipApplication
from app.models.fine       import Fine
from app.models.notification import Notification
from app.models.policy     import Policy


async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Tables created")


async def seed(session: AsyncSession):
    # ── Admins ────────────────────────────────────────────────
    pw = hash_password("admin123")
    admin = Admin(
        name="Super Admin",
        email="admin@campusgpt.edu",
        password_hash=pw,
        role="super_admin",
        department="Administration",
    )
    session.add(admin)
    await session.flush()

    # ── Students ──────────────────────────────────────────────
    spw = hash_password("student123")
    arjun = Student(
        student_id="2024CS001",
        name="Arjun Sharma",
        email="arjun@campusgpt.edu",
        password_hash=spw,
        phone="9876543210",
        date_of_birth=date(2005, 3, 15),
        gender="male",
        course="B.Tech CSE",
        branch="Computer Science",
        semester=3,
        year=2,
        batch=2024,
        section="A",
        category="general",
        is_hostel_student=True,
        guardian_name="Rajesh Sharma",
        guardian_phone="9876543200",
    )
    priya = Student(
        student_id="2024CS002",
        name="Priya Singh",
        email="priya@campusgpt.edu",
        password_hash=spw,
        phone="9876543211",
        date_of_birth=date(2005, 7, 22),
        gender="female",
        course="B.Tech CSE",
        branch="Computer Science",
        semester=3,
        year=2,
        batch=2024,
        section="A",
        category="obc",
        is_hostel_student=False,
    )
    session.add_all([arjun, priya])
    await session.flush()

    # ── Subjects ──────────────────────────────────────────────
    subjects = [
        Subject(code="CS301", name="Data Structures & Algorithms", course="B.Tech CSE", semester=3, credits=4, type="theory"),
        Subject(code="CS302", name="Database Management Systems",  course="B.Tech CSE", semester=3, credits=4, type="theory"),
        Subject(code="CS303", name="Operating Systems",            course="B.Tech CSE", semester=3, credits=3, type="theory"),
        Subject(code="CS304", name="DBMS Lab",                     course="B.Tech CSE", semester=3, credits=2, type="lab"),
        Subject(code="CS305", name="Web Technologies",             course="B.Tech CSE", semester=3, credits=3, type="elective"),
    ]
    session.add_all(subjects)
    await session.flush()

    # ── Attendance Summary (for Arjun – 71%) ──────────────────
    summaries = [
        AttendanceSummary(student_id=arjun.id,  subject_id=subjects[0].id, academic_year="2024-25", semester=3, total_classes=40, attended_classes=29),
        AttendanceSummary(student_id=arjun.id,  subject_id=subjects[1].id, academic_year="2024-25", semester=3, total_classes=38, attended_classes=26),
        AttendanceSummary(student_id=arjun.id,  subject_id=subjects[2].id, academic_year="2024-25", semester=3, total_classes=36, attended_classes=30),
        AttendanceSummary(student_id=arjun.id,  subject_id=subjects[3].id, academic_year="2024-25", semester=3, total_classes=20, attended_classes=18),
        AttendanceSummary(student_id=arjun.id,  subject_id=subjects[4].id, academic_year="2024-25", semester=3, total_classes=35, attended_classes=25),
        AttendanceSummary(student_id=priya.id, subject_id=subjects[0].id, academic_year="2024-25", semester=3, total_classes=40, attended_classes=38),
        AttendanceSummary(student_id=priya.id, subject_id=subjects[1].id, academic_year="2024-25", semester=3, total_classes=38, attended_classes=35),
    ]
    session.add_all(summaries)

    # ── Fees ──────────────────────────────────────────────────
    fees = [
        Fee(student_id=arjun.id, academic_year="2024-25", fee_type="tuition", total_amount=85000, paid_amount=42500, due_date=date(2025, 1, 15)),
        Fee(student_id=arjun.id, academic_year="2024-25", fee_type="hostel",  total_amount=36000, paid_amount=18000, due_date=date(2025, 1, 15)),
        Fee(student_id=arjun.id, academic_year="2024-25", fee_type="exam",    total_amount=2500,  paid_amount=2500,  due_date=date(2024, 11, 30)),
        Fee(student_id=priya.id, academic_year="2024-25", fee_type="tuition", total_amount=85000, paid_amount=85000, due_date=date(2024, 11, 15)),
    ]
    session.add_all(fees)
    await session.flush()

    # ── Hostel ────────────────────────────────────────────────
    room = Hostel(
        hostel_name="Boys Hostel A",
        block="Block-1",
        room_number="101",
        floor=1,
        room_type="double",
        capacity=2,
        monthly_rent=3000,
    )
    session.add(room)
    await session.flush()

    alloc = HostelAllocation(
        student_id=arjun.id,
        hostel_id=room.id,
        allotment_date=date(2024, 7, 15),
        academic_year="2024-25",
        total_fee=36000,
        paid_amount=18000,
        next_due_date=date(2025, 1, 15),
        status="active",
    )
    session.add(alloc)

    # ── Scholarships ──────────────────────────────────────────
    import json
    sch = Scholarship(
        name="Merit Scholarship 2024",
        type="merit",
        amount=25000,
        eligibility_criteria=json.dumps({"min_percentage": 80, "min_attendance": 75}),
        application_start=date(2024, 9, 1),
        application_end=date(2024, 10, 31),
        academic_year="2024-25",
        min_attendance=75,
        min_percentage=80,
        description="For students with 80%+ marks and 75%+ attendance",
    )
    sch2 = Scholarship(
        name="SC/ST Government Scholarship",
        type="government",
        amount=50000,
        eligibility_criteria=json.dumps({"categories": ["sc", "st"]}),
        application_start=date(2024, 8, 1),
        application_end=date(2024, 9, 30),
        academic_year="2024-25",
        min_attendance=75,
        categories_eligible=json.dumps(["sc", "st"]),
        description="Government scholarship for SC/ST students",
    )
    session.add_all([sch, sch2])
    await session.flush()

    # Priya's application
    app_obj = ScholarshipApplication(
        student_id=priya.id,
        scholarship_id=sch.id,
        status="approved",
        approved_amount=25000,
    )
    session.add(app_obj)

    # ── Fines ─────────────────────────────────────────────────
    fine = Fine(
        student_id=arjun.id,
        fine_type="library",
        reason="Overdue library book – 'Introduction to Algorithms' (15 days)",
        amount=150,
        fine_date=date(2024, 11, 10),
        due_date=date(2024, 11, 30),
        imposed_by=admin.id,
    )
    session.add(fine)

    # ── Notifications ─────────────────────────────────────────
    notifs = [
        Notification(
            user_id=arjun.id,
            user_type="student",
            type="attendance_shortage",
            title="⚠️ Attendance Warning",
            message="Your attendance in Web Technologies is 71.4%. Attend the next 5 classes to reach 75%.",
            action_url="/attendance",
            channel="in_app",
        ),
        Notification(
            user_id=arjun.id,
            user_type="student",
            type="fee_due",
            title="💳 Fee Payment Reminder",
            message="Tuition fee of ₹42,500 is due on 15 Jan 2025. Please pay to avoid late fees.",
            action_url="/fees",
            channel="in_app",
        ),
        Notification(
            user_id=arjun.id,
            user_type="student",
            type="fine_reminder",
            title="📚 Library Fine Pending",
            message="You have a pending library fine of ₹150 due on 30 Nov 2024.",
            action_url="/fines",
            channel="in_app",
        ),
    ]
    session.add_all(notifs)

    # ── Demo Policy placeholder ───────────────────────────────
    policy = Policy(
        title="Attendance Policy 2024-25",
        category="attendance",
        file_name="attendance_policy.pdf",
        file_path="uploads/policies/attendance_policy.pdf",
        is_active=True,
        uploaded_by=admin.id,
        summary="Minimum 75% attendance required. Below 65% = detained. Medical leaves handled separately.",
    )
    session.add(policy)

    await session.commit()
    print("✅ Seed data inserted")
    print("\n📋 Demo Credentials:")
    print("   Student:  arjun@campusgpt.edu  /  student123")
    print("   Student:  priya@campusgpt.edu  /  student123")
    print("   Admin:    admin@campusgpt.edu   /  admin123")


async def main():
    print("🚀 Initializing CampusGPT database...")
    await create_tables()
    async with AsyncSessionLocal() as session:
        await seed(session)
    print("\n✅ Database ready! Now run:")
    print("   uvicorn app.main:app --reload")


if __name__ == "__main__":
    asyncio.run(main())
