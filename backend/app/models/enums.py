from enum import Enum


class UserRole(str, Enum):
    rider = "rider"
    driver = "driver"
    admin = "admin"


class Gender(str, Enum):
    male = "male"
    female = "female"
    other = "other"
    prefer_not_to_say = "prefer_not_to_say"


class VerificationStatus(str, Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


class GenderPreference(str, Enum):
    none = "none"
    same_gender = "same_gender"


class RideRequestStatus(str, Enum):
    pending = "pending"
    matched = "matched"
    cancelled = "cancelled"
    completed = "completed"


class TripStatus(str, Enum):
    posted = "posted"
    matched = "matched"
    ongoing = "ongoing"
    completed = "completed"
    cancelled = "cancelled"
    full = "full"


class MatchStatus(str, Enum):
    recommended = "recommended"
    confirmed = "confirmed"
    rejected = "rejected"
    cancelled = "cancelled"
    completed = "completed"


class PaymentStatus(str, Enum):
    pending = "pending"
    paid = "paid"
    failed = "failed"
    refunded = "refunded"


class PaymentMethod(str, Enum):
    simulated_ewallet = "simulated_ewallet"


class SOSStatus(str, Enum):
    new = "new"
    reviewing = "reviewing"
    resolved = "resolved"
    false_alarm = "false_alarm"


class ReportType(str, Enum):
    late = "late"
    unsafe = "unsafe"
    rude = "rude"
    fake_account = "fake_account"
    payment_issue = "payment_issue"
    other = "other"
