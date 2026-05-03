import enum


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    USER = "user"


class CompanyRole(str, enum.Enum):
    OWNER = "owner"
    DRIVER = "driver"


class CompanyType(str, enum.Enum):
    LESSOR = "lessor"
    RENTER = "renter"


class AgreementType(str, enum.Enum):
    PUBLIC_OFFER = "public_offer"
    DRIVER_OFFER = "driver_offer"


class CarStatus(str, enum.Enum):
    AVAILABLE = "AVAILABLE"
    RENTED = "RENTED"
    INACTIVE = "INACTIVE"
    HIDDEN = "HIDDEN"


class RentalRequestStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"


class RentalStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    OVERDUE = "OVERDUE"


class PaymentStatus(str, enum.Enum):
    PENDING = "PENDING"
    PAID = "PAID"
    FAILED = "FAILED"


class PaymentType(str, enum.Enum):
    BALANCE = "BALANCE"
    CARD = "CARD"


class RentalDocumentType(str, enum.Enum):
    ACT = "act"
    INVOICE = "invoice"
    CONTRACT = "contract"


class GeofenceType(str, enum.Enum):
    EXIT = "EXIT"
    ENTER = "ENTER"


class ViolationType(str, enum.Enum):
    GEOFENCE_EXIT = "GEOFENCE_EXIT"
    SPEEDING = "SPEEDING"


class SeverityType(str, enum.Enum):
    WARNING = "WARNING"


class CategoriesType(str, enum.Enum):
    B = "B"
    C = "C"
    D = "D"
