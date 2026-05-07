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

            <p>г. Москва, {now_date}</p>

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
