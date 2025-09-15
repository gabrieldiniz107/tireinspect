from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from django.utils import formats


def gerar_pedido_pdf(order):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    margin = 20 * mm
    x = margin
    y = height - margin

    # Header
    titulo = "ORDEM DE SERVIÇO"
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(x, y, titulo)

    c.setFont("Helvetica", 10)
    y -= 8 * mm
    c.drawString(x, y, f"Nº: {order.service_number or '-'}")
    y -= 6 * mm
    data_fmt = formats.date_format(order.order_date, "DATE_FORMAT") if order.order_date else "-"
    c.drawString(x, y, f"Data: {data_fmt}")

    # Linha separadora
    y -= 6 * mm
    c.setStrokeColor(colors.black)
    c.line(x, y, width - margin, y)

    # Dados principais
    y -= 10 * mm
    c.setFont("Helvetica-Bold", 11)
    c.drawString(x, y, "Dados do cliente e veículo")
    y -= 7 * mm
    c.setFont("Helvetica", 10)

    def draw_row(label, value):
        nonlocal y
        c.setFont("Helvetica-Bold", 10)
        c.drawString(x, y, f"{label}:")
        c.setFont("Helvetica", 10)
        c.drawString(x + 35 * mm, y, value or "-")
        y -= 6 * mm

    draw_row("Cliente", order.client)
    draw_row("CNPJ/CPF", order.cnpj_cpf)

    # Caminhões vinculados
    y -= 4 * mm
    c.setFont("Helvetica-Bold", 11)
    c.drawString(x, y, "Caminhões")
    y -= 7 * mm
    c.setFont("Helvetica", 10)
    trucks = list(order.trucks.all())
    if trucks:
        for idx, t in enumerate(trucks, start=1):
            c.drawString(x, y, f"{idx}. Placa: {t.plate}  •  Frota: {t.fleet or '-'}")
            y -= 6 * mm
            if y < 30 * mm:
                c.showPage(); y = height - margin
    else:
        c.drawString(x, y, "—")

    # Rodapé simples
    c.setFont("Helvetica-Oblique", 8)
    c.setFillColor(colors.grey)
    c.drawRightString(width - margin, margin, "Gerado por TireInspect")

    c.showPage()
    c.save()
    pdf = buffer.getvalue()
    buffer.close()
    return pdf
