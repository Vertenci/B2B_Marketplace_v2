from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import String, Numeric, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Enum as SqlEnum

from src.db.base import Base
from src.models.enums import CompanyType
from src.models.mixin import IdMixin, CreatedAtMixin

if TYPE_CHECKING:
    from src.models.company_users_model import CompanyUserModel
    from src.models.car_model import CarModel
    from src.models.rental_request_model import RentalRequestModel
    from src.models.rental_model import RentalModel
    from src.models.payment_model import PaymentModel


class CompanyModel(Base, IdMixin, CreatedAtMixin):
    __tablename__ = "companies"

    name: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
    )

    inn: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
    )

    type: Mapped[CompanyType] = mapped_column(
        SqlEnum(
            CompanyType,
            name="company_type",
            values_callable=lambda enum: [e.value for e in enum],
        ),
        default=CompanyType.LESSOR,
        nullable=False,
    )

    balance: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        default=0.00,
        nullable=False,
    )

    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    def __str__(self):
        return self.name

    company_users: Mapped[list["CompanyUserModel"]] = relationship("CompanyUserModel", back_populates="company", lazy="raise", uselist=True)

    cars: Mapped[list["CarModel"] | None] = relationship("CarModel", back_populates="company", lazy="raise", uselist=True)

    rental_requests: Mapped[list["RentalRequestModel"] | None] = relationship("RentalRequestModel", back_populates="company", lazy="raise", uselist=True)

    lessor_rentals: Mapped[list["RentalModel"] | None] = relationship("RentalModel", foreign_keys="RentalModel.lessor_company_id", back_populates="lessor_company", lazy="raise", uselist=True)

    renter_rentals: Mapped[list["RentalModel"] | None] = relationship("RentalModel", foreign_keys="RentalModel.renter_company_id", back_populates="renter_company", lazy="raise", uselist=True)

    payer_companies: Mapped[list["PaymentModel"] | None] = relationship("PaymentModel", foreign_keys="PaymentModel.payer_company_id", back_populates="payer_company", lazy="raise", uselist=True)

    receiver_companies: Mapped[list["PaymentModel"] | None] = relationship("PaymentModel", foreign_keys="PaymentModel.receiver_company_id", back_populates="receiver_company", lazy="raise", uselist=True)
