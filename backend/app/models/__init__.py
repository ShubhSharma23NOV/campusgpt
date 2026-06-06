# Import all models to ensure they're registered with SQLAlchemy
from app.models.admin import Admin
from app.models.student import Student
from app.models.attendance import Subject, Attendance, AttendanceSummary
from app.models.fees import Fee, FeePayment
from app.models.hostel import Hostel, HostelAllocation, HostelPayment
from app.models.scholarship import Scholarship, ScholarshipApplication, ScholarshipPayment
from app.models.fine import Fine, FinePayment
from app.models.notification import Notification
from app.models.policy import Policy
