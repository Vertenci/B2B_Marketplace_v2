import asyncio
import io
import logging
from datetime import datetime

from weasyprint import HTML

from src.clients.minio_client import minio_client
from src.models import RentalModel, RentalDocumentsModel
from src.models.enums import RentalDocumentType

logger = logging.getLogger(__name__)


def _generate_contract_html(rental: RentalModel) -> str:
    start_date = rental.start_date.strftime('%d.%m.%Y %H:%M')
    end_date = rental.end_date.strftime('%d.%m.%Y %H:%M')
    now_date = datetime.now().strftime('%d.%m.%Y')

    lessor_name = rental.lessor_company.name if rental.lessor_company else "—"
    lessor_inn  = rental.lessor_company.inn  if rental.lessor_company else "—"
    renter_name = rental.renter_company.name if rental.renter_company else "—"
    renter_inn  = rental.renter_company.inn  if rental.renter_company else "—"
    car_brand   = rental.car.brand           if rental.car else "—"
    car_model   = rental.car.model           if rental.car else "—"
    car_year    = rental.car.year            if rental.car else "—"
    car_plate   = rental.car.plate_number    if rental.car else "—"
    car_vin     = rental.car.vin             if rental.car else "—"
    price_day   = rental.car.price_per_day   if rental.car else 0
    total       = rental.base_price_total

    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="UTF-8">
  <title>Договор аренды</title>
  <style>
    @page {{ size: A4; margin: 2cm; }}
    body {{ font-family: Arial, sans-serif; font-size: 12px; line-height: 1.5; color: #000; }}
    h1 {{ text-align: center; font-size: 18px; margin-bottom: 20px; }}
    h2 {{ font-size: 14px; margin-top: 25px; margin-bottom: 10px; }}
    table {{ width: 100%; border-collapse: collapse; margin: 15px 0; }}
    th, td {{ padding: 8px 10px; border: 1px solid #000; font-size: 12px; }}
    th {{ background: #f0f0f0; font-weight: bold; text-align: left; }}
    .sign-row td {{ border: none; padding: 30px 10px 0; vertical-align: top; width: 50%; }}
  </style>
</head>
<body>
  <h1>ДОГОВОР АРЕНДЫ ТРАНСПОРТНОГО СРЕДСТВА</h1>
  <p style="text-align:right">г. Дата: {now_date}</p>

  <h2>1. Стороны договора</h2>
  <table>
    <tr><th style="width:30%">Арендодатель</th><td><strong>{lessor_name}</strong> ИНН: {lessor_inn}</td></tr>
    <tr><th>Арендатор</th><td><strong>{renter_name}</strong> ИНН: {renter_inn}</td></tr>
  </table>

  <h2>2. Предмет договора</h2>
  <table>
    <tr><th style="width:30%">Автомобиль</th><td>{car_brand} {car_model} {car_year}</td></tr>
    <tr><th>Гос. номер</th><td>{car_plate}</td></tr>
    <tr><th>VIN</th><td>{car_vin}</td></tr>
    <tr><th>Начало аренды</th><td>{start_date}</td></tr>
    <tr><th>Окончание аренды</th><td>{end_date}</td></tr>
    <tr><th>Стоимость/день</th><td>{price_day} руб.</td></tr>
    <tr><th>Итого</th><td><strong>{total} руб.</strong></td></tr>
  </table>

  <h2>3. Подписи сторон</h2>
  <table>
    <tr class="sign-row">
      <td>Арендодатель:<br><br><br>________________________<br><small>{lessor_name}</small></td>
      <td>Арендатор:<br><br><br>________________________<br><small>{renter_name}</small></td>
    </tr>
  </table>
</body>
</html>"""


def _generate_act_html(rental: RentalModel, completed_by: str) -> str:
    start_date  = rental.start_date.strftime('%d.%m.%Y %H:%M')
    end_date    = rental.end_date.strftime('%d.%m.%Y %H:%M')
    actual_date = rental.actual_return_date.strftime('%d.%m.%Y %H:%M') if rental.actual_return_date else "—"
    now_date    = datetime.now().strftime('%d.%m.%Y')
    who         = "Арендодателем" if completed_by == "lessor" else "Арендатором"

    lessor_name = rental.lessor_company.name if rental.lessor_company else "—"
    renter_name = rental.renter_company.name if rental.renter_company else "—"
    car_brand   = rental.car.brand           if rental.car else "—"
    car_model   = rental.car.model           if rental.car else "—"
    car_plate   = rental.car.plate_number    if rental.car else "—"
    base_total  = rental.base_price_total
    extra_fee   = rental.extra_days_fee

    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="UTF-8">
  <title>Акт приёма-передачи</title>
  <style>
    @page {{ size: A4; margin: 2cm; }}
    body {{ font-family: Arial, sans-serif; font-size: 12px; line-height: 1.5; color: #000; }}
    h1 {{ text-align: center; font-size: 16px; margin-bottom: 20px; }}
    table {{ width: 100%; border-collapse: collapse; margin: 15px 0; }}
    th, td {{ padding: 8px 10px; border: 1px solid #000; font-size: 12px; }}
    th {{ background: #f0f0f0; text-align: left; }}
    .sign-row td {{ border: none; padding: 30px 10px 0; vertical-align: top; width: 50%; }}
  </style>
</head>
<body>
  <h1>АКТ ПРИЁМА-ПЕРЕДАЧИ ТРАНСПОРТНОГО СРЕДСТВА</h1>
  <p style="text-align:right">Дата: {now_date} | Завершена {who}</p>

  <table>
    <tr><th style="width:35%">Арендодатель</th><td>{lessor_name}</td></tr>
    <tr><th>Арендатор</th><td>{renter_name}</td></tr>
    <tr><th>Автомобиль</th><td>{car_brand} {car_model} ({car_plate})</td></tr>
    <tr><th>Начало аренды</th><td>{start_date}</td></tr>
    <tr><th>Плановое окончание</th><td>{end_date}</td></tr>
    <tr><th>Фактический возврат</th><td>{actual_date}</td></tr>
    <tr><th>Базовая стоимость</th><td>{base_total} руб.</td></tr>
    <tr><th>Доп. дни (просрочка)</th><td>{extra_fee} руб.</td></tr>
    <tr><th><strong>Итого к оплате</strong></th><td><strong>{float(base_total) + float(extra_fee):.2f} руб.</strong></td></tr>
  </table>

  <table>
    <tr class="sign-row">
      <td>Арендодатель:<br><br><br>________________________<br><small>{lessor_name}</small></td>
      <td>Арендатор:<br><br><br>________________________<br><small>{renter_name}</small></td>
    </tr>
  </table>
</body>
</html>"""


def _generate_invoice_html(rental: RentalModel) -> str:
    now_date    = datetime.now().strftime('%d.%m.%Y')

    lessor_name = rental.lessor_company.name if rental.lessor_company else "—"
    lessor_inn  = rental.lessor_company.inn  if rental.lessor_company else "—"
    renter_name = rental.renter_company.name if rental.renter_company else "—"
    renter_inn  = rental.renter_company.inn  if rental.renter_company else "—"
    car_brand   = rental.car.brand           if rental.car else "—"
    car_model   = rental.car.model           if rental.car else "—"
    car_plate   = rental.car.plate_number    if rental.car else "—"
    base_total  = rental.base_price_total
    extra_fee   = rental.extra_days_fee
    grand_total = float(base_total) + float(extra_fee)

    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="UTF-8">
  <title>Счёт-фактура</title>
  <style>
    @page {{ size: A4; margin: 2cm; }}
    body {{ font-family: Arial, sans-serif; font-size: 12px; line-height: 1.5; color: #000; }}
    h1 {{ text-align: center; font-size: 16px; margin-bottom: 20px; }}
    table {{ width: 100%; border-collapse: collapse; margin: 15px 0; }}
    th, td {{ padding: 8px 10px; border: 1px solid #000; font-size: 12px; }}
    th {{ background: #f0f0f0; text-align: left; }}
    .sign-row td {{ border: none; padding: 30px 10px 0; vertical-align: top; width: 50%; }}
  </style>
</head>
<body>
  <h1>СЧЁТ-ФАКТУРА № {str(rental.id)[:8].upper()}</h1>
  <p style="text-align:right">Дата: {now_date}</p>

  <table>
    <tr><th style="width:35%">Продавец (Арендодатель)</th><td>{lessor_name}, ИНН: {lessor_inn}</td></tr>
    <tr><th>Покупатель (Арендатор)</th><td>{renter_name}, ИНН: {renter_inn}</td></tr>
  </table>

  <table>
    <tr>
      <th>Наименование</th><th>Ед.</th><th>Кол-во</th><th>Сумма</th>
    </tr>
    <tr>
      <td>Аренда {car_brand} {car_model} ({car_plate})</td>
      <td>услуга</td><td>1</td><td>{base_total} руб.</td>
    </tr>
    <tr>
      <td>Доп. дни (просрочка)</td>
      <td>услуга</td><td>1</td><td>{extra_fee} руб.</td>
    </tr>
    <tr>
      <td colspan="3"><strong>ИТОГО:</strong></td>
      <td><strong>{grand_total:.2f} руб.</strong></td>
    </tr>
  </table>

  <table>
    <tr class="sign-row">
      <td>Продавец:<br><br><br>________________________<br><small>{lessor_name}</small></td>
      <td>Покупатель:<br><br><br>________________________<br><small>{renter_name}</small></td>
    </tr>
  </table>
</body>
</html>"""


class ContractService:
    @staticmethod
    def _make_pdf(html: str) -> bytes:
        result = HTML(string=html).write_pdf()
        return result or b""

    @staticmethod
    async def generate_and_upload_contract(rental_id: str) -> None:
        from src.db.session import db
        from sqlalchemy import select
        from sqlalchemy.orm import joinedload

        try:
            async with db.session_factory() as session:
                stmt = (
                    select(RentalModel)
                    .where(RentalModel.id == rental_id)
                    .options(
                        joinedload(RentalModel.lessor_company),
                        joinedload(RentalModel.renter_company),
                        joinedload(RentalModel.car),
                    )
                )
                result = await session.execute(stmt)
                rental = result.unique().scalar_one_or_none()
                if not rental:
                    logger.error(f"[Contract] Rental {rental_id} not found")
                    return

                loop = asyncio.get_running_loop()
                html = _generate_contract_html(rental)
                pdf_bytes = await loop.run_in_executor(
                    None, ContractService._make_pdf, html
                )

                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                object_name = f"rental_documents/{rental_id}/contract_{timestamp}.pdf"

                await minio_client.upload_file(
                    file_data=io.BytesIO(pdf_bytes),
                    object_name=object_name,
                    content_type="application/pdf",
                    metadata={"rental-id": str(rental_id), "document-type": "contract"},
                )

                doc = RentalDocumentsModel(
                    rental_id=rental.id,
                    type=RentalDocumentType.CONTRACT,
                    file_path=object_name,
                )
                session.add(doc)
                await session.commit()
                logger.info(f"[Contract] Generated for rental {rental_id}: {object_name}")

        except Exception as exc:
            logger.exception(f"[Contract] Failed to generate contract for rental {rental_id}: {exc}")

    @staticmethod
    async def generate_and_upload_act(rental_id: str, completed_by: str = "lessor") -> None:
        from src.db.session import db
        from sqlalchemy import select
        from sqlalchemy.orm import joinedload

        try:
            async with db.session_factory() as session:
                stmt = (
                    select(RentalModel)
                    .where(RentalModel.id == rental_id)
                    .options(
                        joinedload(RentalModel.lessor_company),
                        joinedload(RentalModel.renter_company),
                        joinedload(RentalModel.car),
                    )
                )
                result = await session.execute(stmt)
                rental = result.unique().scalar_one_or_none()
                if not rental:
                    logger.error(f"[Act] Rental {rental_id} not found")
                    return

                loop = asyncio.get_running_loop()
                html = _generate_act_html(rental, completed_by)
                pdf_bytes = await loop.run_in_executor(
                    None, ContractService._make_pdf, html
                )

                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                object_name = f"rental_documents/{rental_id}/act_{timestamp}.pdf"

                await minio_client.upload_file(
                    file_data=io.BytesIO(pdf_bytes),
                    object_name=object_name,
                    content_type="application/pdf",
                    metadata={"rental-id": str(rental_id), "document-type": "act"},
                )

                doc = RentalDocumentsModel(
                    rental_id=rental.id,
                    type=RentalDocumentType.ACT,
                    file_path=object_name,
                )
                session.add(doc)
                await session.commit()
                logger.info(f"[Act] Generated for rental {rental_id}: {object_name}")

        except Exception as exc:
            logger.exception(f"[Act] Failed to generate act for rental {rental_id}: {exc}")

    @staticmethod
    async def generate_and_upload_invoice(rental_id: str) -> None:
        from src.db.session import db
        from sqlalchemy import select
        from sqlalchemy.orm import joinedload

        try:
            async with db.session_factory() as session:
                stmt = (
                    select(RentalModel)
                    .where(RentalModel.id == rental_id)
                    .options(
                        joinedload(RentalModel.lessor_company),
                        joinedload(RentalModel.renter_company),
                        joinedload(RentalModel.car),
                    )
                )
                result = await session.execute(stmt)
                rental = result.unique().scalar_one_or_none()
                if not rental:
                    logger.error(f"[Invoice] Rental {rental_id} not found")
                    return

                loop = asyncio.get_running_loop()
                html = _generate_invoice_html(rental)
                pdf_bytes = await loop.run_in_executor(
                    None, ContractService._make_pdf, html
                )

                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                object_name = f"rental_documents/{rental_id}/invoice_{timestamp}.pdf"

                await minio_client.upload_file(
                    file_data=io.BytesIO(pdf_bytes),
                    object_name=object_name,
                    content_type="application/pdf",
                    metadata={"rental-id": str(rental_id), "document-type": "invoice"},
                )

                doc = RentalDocumentsModel(
                    rental_id=rental.id,
                    type=RentalDocumentType.INVOICE,
                    file_path=object_name,
                )
                session.add(doc)
                await session.commit()
                logger.info(f"[Invoice] Generated for rental {rental_id}: {object_name}")

        except Exception as exc:
            logger.exception(f"[Invoice] Failed to generate invoice for rental {rental_id}: {exc}")
