from typing import Any
from sqladmin import ModelView
from starlette.requests import Request
from sqlalchemy.orm.exc import StaleDataError
from sqlalchemy.exc import IntegrityError


class BaseAdmin(ModelView):
    async def insert_model(self, request: Request, data: dict):
        try:
            return await super().insert_model(request, data)

        except IntegrityError as e:
            if "uq_company_user" in str(e.orig):
                raise ValueError(
                    "This user is already assigned to this company."
                )

            raise ValueError("Database integrity error.")

    async def update_model(self, request: Request, pk: Any, data: dict):
        try:
            return await super().update_model(request, pk, data)

        except IntegrityError as e:
            if "uq_company_user" in str(e.orig):
                raise ValueError(
                    "This user is already assigned to this company."
                )

            raise ValueError("Database integrity error.")

    async def on_model_change(self, data, model, is_created, request: Request):
        try:
            return await super().on_model_change(
                data,
                model,
                is_created,
                request
            )

        except StaleDataError:
            raise ValueError("Record was modified by another user.")
