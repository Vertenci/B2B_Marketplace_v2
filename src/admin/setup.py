from fastapi import FastAPI
from sqladmin import Admin
from starlette.middleware.sessions import SessionMiddleware

from src.admin.auth import AdminAuth
from src.admin.views.agreement_admin import AgreementAdmin
from src.admin.views.car_admin import CarAdmin
from src.admin.views.company_admin import CompanyAdmin
from src.admin.views.company_user_admin import CompanyUserAdmin
from src.admin.views.document_admin import DocumentAdmin
from src.admin.views.driver_license_admin import DriverLicenseAdmin
from src.admin.views.geofence_admin import GeofenceAdmin
from src.admin.views.geofence_event_admin import GeofenceEventAdmin
from src.admin.views.iot_device_admin import IotDeviceAdmin
from src.admin.views.payment_admin import PaymentAdmin
from src.admin.views.refresh_token_admin import RefreshTokenAdmin
from src.admin.views.rental_admin import RentalAdmin
from src.admin.views.rental_document_admin import RentalDocumentsAdmin
from src.admin.views.rental_request_admin import RentalRequestAdmin
from src.admin.views.telemetry_admin import TelemetryAdmin
from src.admin.views.user_admin import UserAdmin
from src.admin.views.violation_admin import ViolationAdmin
from src.core.settings import settings
from src.db.database import Database


def setup_admin(app: FastAPI, db: Database):
    app.add_middleware(SessionMiddleware, secret_key=settings.ADMIN_SECRET_KEY)

    admin = Admin(
        app=app,
        engine=db.engine,
        authentication_backend=AdminAuth(secret_key=settings.ADMIN_SECRET_KEY),
    )

    # Accounts
    admin.add_view(UserAdmin)
    admin.add_view(DriverLicenseAdmin)

    # Companies
    admin.add_view(CompanyAdmin)
    admin.add_view(CompanyUserAdmin)

    # Documents
    admin.add_view(AgreementAdmin)
    admin.add_view(DocumentAdmin)

    # Fleet
    admin.add_view(CarAdmin)
    admin.add_view(GeofenceEventAdmin)
    admin.add_view(GeofenceAdmin)

    # IoT
    admin.add_view(IotDeviceAdmin)
    admin.add_view(TelemetryAdmin)

    # Finance
    admin.add_view(PaymentAdmin)

    # Security
    admin.add_view(RefreshTokenAdmin)

    # Rentals
    admin.add_view(RentalDocumentsAdmin)
    admin.add_view(RentalAdmin)
    admin.add_view(RentalRequestAdmin)
    admin.add_view(ViolationAdmin)

    return admin
