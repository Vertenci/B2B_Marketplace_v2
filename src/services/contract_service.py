import asyncio
import io
import logging
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from weasyprint import HTML

from src.clients.minio_client import minio_client
from src.models import RentalModel, RentalDocumentsModel
from src.models.enums import RentalDocumentType



logger = logging.getLogger(__name__)


class ContractService:
    @staticmethod
    def _generate_contract_html(rental: RentalModel) -> str:
        start_date = rental.start_date.strftime('%d.%m.%Y %H:%M')
        end_date = rental.end_date.strftime('%d.%m.%Y %H:%M')
        now_date = datetime.now().strftime('%d.%m.%Y')

        return f"""
        <!DOCTYPE html>
        <html lang="ru">
        <head>
            <meta charset="UTF-8">
            <title>Договор аренды автомобиля</title>
            <style>
                @page {{
                    size: A4;
                    margin: 2cm;
                }}
                body {{
                    font-family: 'Arial', sans-serif;
                    font-size: 12px;
                    line-height: 1.5;
                    color: #000;
                }}
                h1 {{
                    text-align: center;
                    font-size: 18px;
                    margin-bottom: 20px;
                }}
                h2 {{
                    font-size: 14px;
                    margin-top: 25px;
                    margin-bottom: 10px;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin: 15px 0;
                }}
                th, td {{
                    padding: 8px 10px;
                    border: 1px solid #000;
                    text-align: left;
                    font-size: 12px;
                }}
                th {{
                    background-color: #f0f0f0;
                    width: 200px;
                }}
                p {{
                    margin: 8px 0;
                }}
                .signature-table {{
                    margin-top: 50px;
                }}
                .signature-table td {{
                    border: none;
                    padding: 30px 10px 0 10px;
                    vertical-align: top;
                    width: 50%;
                }}
                .signature-line {{
                    border-bottom: 1px solid #000;
                    margin-top: 30px;
                }}
            </style>
        </head>
        <body>
            <h1>ДОГОВОР АРЕНДЫ АВТОМОБИЛЯ №{rental.id}</h1>

            <p>г. Минск, {now_date}</p>

            <h2>1. Стороны договора</h2>
            <table>
                <tr>
                    <th>Арендодатель (LESSOR)</th>
                    <td>
                        <strong>{rental.lessor_company.name}</strong><br>
                        ИНН: {rental.lessor_company.inn}
                    </td>
                </tr>
                <tr>
                    <th>Арендатор (RENTER)</th>
                    <td>
                        <strong>{rental.renter_company.name}</strong><br>
                        ИНН: {rental.renter_company.inn}
                    </td>
                </tr>
            </table>

            <h2>2. Автомобиль</h2>
            <table>
                <tr>
                    <th>Марка и модель</th>
                    <td>{rental.car.brand} {rental.car.model}</td>
                </tr>
                <tr>
                    <th>Год выпуска</th>
                    <td>{rental.car.year}</td>
                </tr>
                <tr>
                    <th>Гос. номер</th>
                    <td>{rental.car.plate_number}</td>
                </tr>
                <tr>
                    <th>VIN</th>
                    <td>{rental.car.vin}</td>
                </tr>
            </table>

            <h2>3. Условия аренды</h2>
            <table>
                <tr>
                    <th>Водитель</th>
                    <td>{rental.user.full_name}</td>
                </tr>
                <tr>
                    <th>Начало аренды</th>
                    <td>{start_date}</td>
                </tr>
                <tr>
                    <th>Конец аренды</th>
                    <td>{end_date}</td>
                </tr>
                <tr>
                    <th>Стоимость аренды</th>
                    <td>{rental.base_price_total:,.2f} ₽</td>
                </tr>
            </table>

            <table class="signature-table">
                <tr>
                    <td>
                        <strong>Арендодатель:</strong><br><br>
                        <div class="signature-line"></div>
                        <small>{rental.lessor_company.name}</small>
                    </td>
                    <td>
                        <strong>Арендатор:</strong><br><br>
                        <div class="signature-line"></div>
                        <small>{rental.renter_company.name}</small>
                    </td>
                </tr>
            </table>
        </body>
        </html>
        """

    @staticmethod
    def _generate_pdf_bytes(rental: RentalModel) -> bytes:

        html_content = ContractService._generate_contract_html(rental)

        pdf_bytes = HTML(string=html_content).write_pdf()
        return pdf_bytes

    @staticmethod
    async def generate_and_upload_contract(
            rental: RentalModel,
            session: AsyncSession
    ) -> RentalDocumentsModel:
        import asyncio

        loop = asyncio.get_event_loop()
        pdf_bytes = await loop.run_in_executor(
            None,
            ContractService._generate_pdf_bytes,
            rental
        )

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        object_name = f"rental_documents/{rental.id}/contract_{timestamp}.pdf"

        pdf_file = io.BytesIO(pdf_bytes)
        await minio_client.upload_file(
            file_data=pdf_file,
            object_name=object_name,
            content_type="application/pdf",
            metadata={
                "rental_id": str(rental.id),
                "document_type": "contract",
                "lessor_company": rental.lessor_company.name,
                "renter_company": rental.renter_company.name,
            }
        )

        document = RentalDocumentsModel(
            rental_id=rental.id,
            type=RentalDocumentType.CONTRACT,
            file_path=object_name,
        )
        session.add(document)
        await session.commit()
        await session.refresh(document)

        logger.info(f"Contract generated and uploaded for rental {rental.id}: {object_name}")
        return document

    @staticmethod
    def _generate_act_html(rental: RentalModel, completed_by: str) -> str:
        start_date = rental.start_date.strftime('%d.%m.%Y %H:%M')
        end_date = rental.end_date.strftime('%d.%m.%Y %H:%M')
        actual_date = rental.actual_return_date.strftime('%d.%m.%Y %H:%M') if rental.actual_return_date else "—"
        now_date = datetime.now().strftime('%d.%m.%Y')
        completed_text = "Арендодателем" if completed_by == "lessor" else "Арендатором"

        return f"""
        <!DOCTYPE html>
        <html lang="ru">
        <head>
            <meta charset="UTF-8">
            <title>Акт приёма-передачи автомобиля</title>
            <style>
                @page {{ size: A4; margin: 2cm; }}
                body {{ font-family: 'Arial', sans-serif; font-size: 12px; line-height: 1.5; }}
                h1 {{ text-align: center; font-size: 16px; margin-bottom: 20px; }}
                table {{ width: 100%; border-collapse: collapse; margin: 15px 0; }}
                th, td {{ padding: 8px 10px; border: 1px solid #000; text-align: left; font-size: 12px; }}
                th {{ background-color: #f0f0f0; width: 250px; }}
                .signature-table {{ margin-top: 50px; }}
                .signature-table td {{ border: none; padding: 30px 10px 0 10px; vertical-align: top; width: 50%; }}
                .signature-line {{ border-bottom: 1px solid #000; margin-top: 30px; }}
            </style>
        </head>
        <body>
            <h1>АКТ ПРИЁМА-ПЕРЕДАЧИ АВТОМОБИЛЯ<br>к договору аренды №{rental.id}</h1>

            <p>г. Минск, {now_date}</p>

            <p>Настоящий акт составлен о том, что автомобиль возвращён {completed_text}.</p>

            <table>
                <tr><th>Арендодатель</th><td>{rental.lessor_company.name} (ИНН: {rental.lessor_company.inn})</td></tr>
                <tr><th>Арендатор</th><td>{rental.renter_company.name} (ИНН: {rental.renter_company.inn})</td></tr>
                <tr><th>Автомобиль</th><td>{rental.car.brand} {rental.car.model}, гос. номер {rental.car.plate_number}, VIN: {rental.car.vin}</td></tr>
                <tr><th>Водитель</th><td>{rental.user.full_name}</td></tr>
                <tr><th>Период аренды</th><td>с {start_date} по {end_date}</td></tr>
                <tr><th>Фактическая дата возврата</th><td>{actual_date}</td></tr>
                <tr><th>Стоимость аренды</th><td>{rental.base_price_total:,.2f} ₽</td></tr>
                <tr><th>Доплата за просрочку</th><td>{rental.extra_days_fee:,.2f} ₽</td></tr>
                <tr><th>Статус оплаты</th><td>{"Оплачено" if rental.is_paid else "Не оплачено"}</td></tr>
            </table>

            <p>Автомобиль возвращён в исправном состоянии. Стороны претензий друг к другу не имеют.</p>

            <table class="signature-table">
                <tr>
                    <td>
                        <strong>Арендодатель:</strong><br><br>
                        <div class="signature-line"></div>
                        <small>{rental.lessor_company.name}</small>
                    </td>
                    <td>
                        <strong>Арендатор:</strong><br><br>
                        <div class="signature-line"></div>
                        <small>{rental.renter_company.name}</small>
                    </td>
                </tr>
            </table>
        </body>
        </html>
        """

    @staticmethod
    def _generate_invoice_html(rental: RentalModel) -> str:
        now_date = datetime.now().strftime('%d.%m.%Y')
        total = rental.base_price_total + rental.extra_days_fee

        return f"""
        <!DOCTYPE html>
        <html lang="ru">
        <head>
            <meta charset="UTF-8">
            <title>Счёт-фактура</title>
            <style>
                @page {{ size: A4; margin: 2cm; }}
                body {{ font-family: 'Arial', sans-serif; font-size: 12px; line-height: 1.5; }}
                h1 {{ text-align: center; font-size: 16px; margin-bottom: 20px; }}
                table {{ width: 100%; border-collapse: collapse; margin: 15px 0; }}
                th, td {{ padding: 8px 10px; border: 1px solid #000; text-align: left; font-size: 12px; }}
                th {{ background-color: #f0f0f0; width: 250px; }}
                .total {{ font-weight: bold; font-size: 14px; }}
            </style>
        </head>
        <body>
            <h1>СЧЁТ-ФАКТУРА №{rental.id}<br>к договору аренды №{rental.id}</h1>

            <p>г. Минск, {now_date}</p>

            <table>
                <tr><th>Продавец</th><td>{rental.lessor_company.name}<br>ИНН: {rental.lessor_company.inn}</td></tr>
                <tr><th>Покупатель</th><td>{rental.renter_company.name}<br>ИНН: {rental.renter_company.inn}</td></tr>
                <tr><th>Основание</th><td>Договор аренды автомобиля №{rental.id}</td></tr>
                <tr><th>Автомобиль</th><td>{rental.car.brand} {rental.car.model}, {rental.car.plate_number}</td></tr>
                <tr><th>Период аренды</th><td>{rental.start_date.strftime('%d.%m.%Y %H:%M')} — {rental.end_date.strftime('%d.%m.%Y %H:%M')}</td></tr>
            </table>

            <table>
                <tr>
                    <th>№</th>
                    <th>Наименование</th>
                    <th>Сумма</th>
                </tr>
                <tr>
                    <td>1</td>
                    <td>Аренда автомобиля за период</td>
                    <td>{rental.base_price_total:,.2f} ₽</td>
                </tr>
                <tr>
                    <td>2</td>
                    <td>Доплата за просрочку</td>
                    <td>{rental.extra_days_fee:,.2f} ₽</td>
                </tr>
                <tr class="total">
                    <td colspan="2">ИТОГО:</td>
                    <td>{total:,.2f} ₽</td>
                </tr>
            </table>

            <p>Статус оплаты: {"Оплачено" if rental.is_paid else "Не оплачено"}</p>

            <table class="signature-table" style="margin-top: 50px;">
                <tr>
                    <td style="border: none; padding: 30px 10px 0 10px; vertical-align: top; width: 50%;">
                        <strong>Продавец:</strong><br><br>
                        <div class="signature-line" style="border-bottom: 1px solid #000; margin-top: 30px;"></div>
                        <small>{rental.lessor_company.name}</small>
                    </td>
                    <td style="border: none; padding: 30px 10px 0 10px; vertical-align: top; width: 50%;">
                        <strong>Покупатель:</strong><br><br>
                        <div class="signature-line" style="border-bottom: 1px solid #000; margin-top: 30px;"></div>
                        <small>{rental.renter_company.name}</small>
                    </td>
                </tr>
            </table>
        </body>
        </html>
        """

    @staticmethod
    async def generate_and_upload_act(
            rental: RentalModel,
            completed_by: str,
            session: AsyncSession
    ) -> RentalDocumentsModel:
        loop = asyncio.get_event_loop()

        def generate_act_pdf():
            html_content = ContractService._generate_act_html(rental, completed_by)
            return HTML(string=html_content).write_pdf()

        pdf_bytes = await loop.run_in_executor(None, generate_act_pdf)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        object_name = f"rental_documents/{rental.id}/act_{timestamp}.pdf"

        pdf_file = io.BytesIO(pdf_bytes)
        await minio_client.upload_file(
            file_data=pdf_file,
            object_name=object_name,
            content_type="application/pdf",
            metadata={
                "rental_id": str(rental.id),
                "document_type": "act",
                "completed_by": completed_by,
            }
        )

        document = RentalDocumentsModel(
            rental_id=rental.id,
            type=RentalDocumentType.ACT,
            file_path=object_name,
        )
        session.add(document)
        await session.commit()
        await session.refresh(document)

        logger.info(f"Act generated for rental {rental.id}: {object_name}")
        return document

    @staticmethod
    async def generate_and_upload_invoice(
            rental: RentalModel,
            session: AsyncSession
    ) -> RentalDocumentsModel:

        import asyncio

        loop = asyncio.get_event_loop()

        def generate_invoice_pdf():
            html_content = ContractService._generate_invoice_html(rental)
            return HTML(string=html_content).write_pdf()

        pdf_bytes = await loop.run_in_executor(None, generate_invoice_pdf)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        object_name = f"rental_documents/{rental.id}/invoice_{timestamp}.pdf"

        pdf_file = io.BytesIO(pdf_bytes)
        await minio_client.upload_file(
            file_data=pdf_file,
            object_name=object_name,
            content_type="application/pdf",
            metadata={
                "rental_id": str(rental.id),
                "document_type": "invoice",
            }
        )

        document = RentalDocumentsModel(
            rental_id=rental.id,
            type=RentalDocumentType.INVOICE,
            file_path=object_name,
        )
        session.add(document)
        await session.commit()
        await session.refresh(document)

        logger.info(f"Invoice generated for rental {rental.id}: {object_name}")
        return document
