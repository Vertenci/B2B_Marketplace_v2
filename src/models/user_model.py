from typing import TYPE_CHECKING

from sqlalchemy import String, Boolean, Text
from sqlalchemy import Enum as SqlEnum
from sqlalchemy.orm import Mapped, mapped_column, validates, relationship

from src.core.security import hash_password
from src.db.base import Base
from src.models.enums import UserRole
from src.models.mixin import IdMixin, CreatedAtMixin

if TYPE_CHECKING:
    from src.models.company_users_model import CompanyUserModel
    from src.models.agreement_model import AgreementModel
    from src.models.rental_request_model import RentalRequestModel
    from src.models.rental_model import RentalModel
    from src.models.telemetry_model import TelemetryModel
    from src.models.driver_license_model import DriverLicenseModel
    from src.models.refresh_token_model import RefreshTokenModel


class UserModel(Base, IdMixin, CreatedAtMixin):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
    )

    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    phone: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        unique=True,
    )

    full_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    role: Mapped[UserRole] = mapped_column(
        SqlEnum(
            UserRole,
            name="user_role",
            values_callable=lambda enum: [e.value for e in enum],
        ),
        default=UserRole.USER,
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    public_offer_accepted: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    @property
    def password(self):
        raise AttributeError("Password is write-only")

    @password.setter
    def password(self, raw_password: str):
        self.password_hash = hash_password(raw_password)

    @validates("email")
    def normalize_email(self, key: str, value: str) -> str:
        return value.strip().lower()

    def __str__(self):
        return self.email

    company_users: Mapped[list["CompanyUserModel"]] = relationship("CompanyUserModel", back_populates="user", lazy="raise", uselist=True)

    agreements: Mapped[list["AgreementModel"]] = relationship("AgreementModel", back_populates="user", lazy="raise", uselist=True)

    rental_requests: Mapped[list["RentalRequestModel"]] = relationship("RentalRequestModel", back_populates="user", lazy="raise", uselist=True)

    rentals: Mapped[list["RentalModel"]] = relationship("RentalModel", back_populates="user", lazy="raise", uselist=True)

    telemetries: Mapped[list["TelemetryModel"]] = relationship("TelemetryModel", back_populates="user", lazy="raise",  uselist=True)

    driver_license: Mapped["DriverLicenseModel | None"] = relationship("DriverLicenseModel", back_populates="user", lazy="raise", uselist=False)

    refresh_tokens: Mapped[list["RefreshTokenModel"]] = relationship("RefreshTokenModel", back_populates="user", lazy="raise", uselist=True)
