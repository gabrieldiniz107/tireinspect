# reports/utils.py

import os
import io
from io import BytesIO
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.lib.colors import Color
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
)
from reportlab.lib.enums import TA_CENTER

from PyPDF2 import PdfMerger

from core.views import gerar_posicoes_personalizadas


def gerar_inspecao_pdf(inspecao):
    """
    Gera o PDF de uma única inspeção (bytes).
    """
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # cores base
    cor_prim     = Color(1, 0.82, 0, 1)
    cor_sec      = Color(0.22, 0.26, 0.3, 1)
    cor_claro    = Color(0.9, 0.9, 0.9, 1)
    cor_verde    = Color(0, 0.7, 0, 1)
    cor_vermelho = Color(0.8, 0, 0, 1)

    # margens
    margin_left   = 15 * mm
    margin_right  = 15 * mm
    margin_top    = 15 * mm
    margin_bottom = 15 * mm
    content_width = width - margin_left - margin_right

    # cabeçalho
    logo = os.path.join("static", "img", "checkUpPneus_logo.png")
    if os.path.exists(logo):
        p.drawImage(ImageReader(logo), margin_left, height - 35 * mm, 35 * mm, 17 * mm, mask="auto")

    p.setFillColor(cor_sec)
    p.setFont("Helvetica-Bold", 14)
    p.drawString(margin_left + 40 * mm, height - 20 * mm, "INSPEÇÃO DE VEÍCULO")
    p.setFont("Helvetica-Bold", 11)
    p.drawString(margin_left + 40 * mm, height - 28 * mm, f"Caminhão: {inspecao.truck.plate}")
    p.setFont("Helvetica", 9)
    p.drawString(margin_left + 40 * mm, height - 35 * mm, f"Data: {inspecao.date:%d/%m/%Y}")
    p.drawString(margin_left + 90 * mm, height - 35 * mm, f"Hodômetro: {inspecao.odometer or '—'} km")

    # divisor
    p.setStrokeColor(cor_prim)
    p.setLineWidth(1)
    p.line(margin_left, height - 40 * mm, width - margin_right, height - 40 * mm)

    y = height - 45 * mm

    # DADOS DA INSPEÇÃO
    p.setFillColor(cor_prim)
    p.rect(margin_left, y, content_width, 7 * mm, fill=1)
    p.setFillColor(cor_sec)
    p.setFont("Helvetica-Bold", 9)
    p.drawString(margin_left + 2 * mm, y + 2 * mm, "DADOS DA INSPEÇÃO")
    y -= 12 * mm

    p.setFont("Helvetica", 8)
    if inspecao.notes:
        notes = inspecao.notes.split()
        lines = []
        current = ""
        maxw = content_width - 4 * mm
        for w in notes:
            test = (current + " " + w).strip()
            if p.stringWidth(test, "Helvetica", 8) <= maxw:
                current = test
            else:
                lines.append(current)
                current = w
        if current:
            lines.append(current)
        for line in lines[:3]:
            prefix = "Observações: " if line == lines[0] else " " * 12
            p.drawString(margin_left + 2 * mm, y, prefix + line)
            y -= 4 * mm

    # RELATÓRIO DE PNEUS
    y -= 5 * mm
    p.setFillColor(cor_prim)
    p.rect(margin_left, y, content_width, 7 * mm, fill=1)
    p.setFillColor(cor_sec)
    p.setFont("Helvetica-Bold", 9)
    p.drawString(margin_left + 2 * mm, y + 2 * mm, "RELATÓRIO DE PNEUS")
    y -= 10 * mm

    # montar tabela de pneus
    tt     = inspecao.truck.truck_type
    labels = gerar_posicoes_personalizadas(tt.axle_count, tt.tire_count)
    tires  = inspecao.tires.all().order_by("position")

    headers = ["Pos.", "Sulco F", "Sulco M", "Sulco D", "Marca", "Desenho", "Nº Fogo", "DOT", "Novo"]
    data    = [headers]

    for idx, t in enumerate(tires):
        label = labels[idx] if idx < len(labels) else str(t.position)
        g1, g2, g3 = t.groove_1, t.groove_2, t.groove_3
        grooves = ( [g3, g2, g1] if label.endswith("E") else [g1, g2, g3] )
        data.append([
            label,
            grooves[0] or "—",
            grooves[1] or "—",
            grooves[2] or "—",
            (t.brand or "—")[:8],
            (t.pattern or "—")[:8],
            (t.fire_number or "—")[:8],
            (t.dot or "—")[:6],
            "✓" if t.rec else "✗",
        ])

    colw = [18*mm, 18*mm, 18*mm, 18*mm, 24*mm, 24*mm, 24*mm, 20*mm, 14*mm]
    if sum(colw) > content_width:
        factor = content_width / sum(colw)
        colw   = [w * factor for w in colw]

    table = Table(data, colWidths=colw)
    style = [
        ("BACKGROUND", (0,0), (-1,0), cor_sec),
        ("TEXTCOLOR",  (0,0), (-1,0), colors.white),
        ("ALIGN",      (0,0), (-1,-1), "CENTER"),
        ("VALIGN",     (0,0), (-1,-1), "MIDDLE"),
        ("GRID",       (0,0), (-1,-1), 0.5, colors.grey),
        ("ROWBACKGROUNDS", (0,1),(-1,-1), [colors.white, Color(0.9,0.9,0.9,1)]),
        ("FONTSIZE",   (0,0), (-1,-1), 8),
        ("FONTNAME",   (0,0), (-1,0), "Helvetica-Bold"),
        ("LEFTPADDING",  (0,0),(-1,-1),2),
        ("RIGHTPADDING", (0,0),(-1,-1),2),
        ("TOPPADDING",   (0,0),(-1,-1),3),
        ("BOTTOMPADDING",(0,0),(-1,-1),3),
    ]
    for row in range(1, len(data)):
        color = cor_verde if data[row][-1] == "✓" else cor_vermelho
        style.append(("TEXTCOLOR", (8,row), (8,row), color))
    table.setStyle(TableStyle(style))

    table.wrapOn(p, content_width, height)
    row_h = 8 * mm
    total_h = len(data) * row_h

    if y - total_h < margin_bottom + 20*mm:
        p.showPage()
        y = height - margin_top
        p.setFillColor(cor_prim)
        p.rect(margin_left, y, content_width, 7*mm, fill=1)
        p.setFillColor(cor_sec)
        p.setFont("Helvetica-Bold", 9)
        p.drawString(margin_left + 2*mm, y+2*mm, "RELATÓRIO DE PNEUS (continuação)")
        y -= 12*mm

    table.drawOn(p, margin_left, y - total_h)
    y -= total_h + 15*mm

    # diagrama de pneus
    imgf = f"ca-{tt.axle_count}eixos_{tt.tire_count}pneus.png"
    imgp = os.path.join("static","img", imgf)
    label = f"{tt.axle_count} eixos / {tt.tire_count} pneus"
    if tt.axle_count >= 3 and os.path.exists(imgp):
        p.showPage()
        p.drawImage(ImageReader(imgp),0,0,width,height,mask="auto")
    else:
        p.setFont("Helvetica-Bold",12)
        p.setFillColor(cor_sec)
        lw = p.stringWidth(label,"Helvetica-Bold",12)
        p.drawString((width-lw)/2, y+3*mm, label)
        if os.path.exists(imgp):
            iw, ih = 80*mm,80*mm
            x = (width-iw)/2
            p.drawImage(ImageReader(imgp),x,y-ih,iw,ih,mask="auto")
        else:
            p.setFillColor(Color(0.9,0.9,0.9,1))
            size = 50*mm
            x = (width-size)/2
            p.rect(x,y-size,size,size,fill=1)
            p.setFillColor(cor_sec)
            p.setFont("Helvetica",8)
            p.drawString(x+10*mm, y-size/2, "Diagrama não disponível")

    p.showPage()
    p.save()
    buffer.seek(0)
    return buffer.getvalue()


def gerar_indice_pdf(inspections):
    """
    Gera página de índice com a mesma identidade visual dos PDFs individuais.
    """
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # cores base (mesmas dos PDFs individuais)
    cor_prim     = Color(1, 0.82, 0, 1)
    cor_sec      = Color(0.22, 0.26, 0.3, 1)
    cor_claro    = Color(0.9, 0.9, 0.9, 1)

    # margens
    margin_left   = 15 * mm
    margin_right  = 15 * mm
    margin_top    = 15 * mm
    margin_bottom = 15 * mm
    content_width = width - margin_left - margin_right

    # cabeçalho com logo
    logo = os.path.join("static", "img", "checkUpPneus_logo.png")
    if os.path.exists(logo):
        p.drawImage(ImageReader(logo), margin_left, height - 35 * mm, 35 * mm, 17 * mm, mask="auto")

    p.setFillColor(cor_sec)
    p.setFont("Helvetica-Bold", 14)
    p.drawString(margin_left + 40 * mm, height - 20 * mm, "RELATÓRIO DE INSPEÇÕES")
    p.setFont("Helvetica", 9)
    p.drawString(margin_left + 40 * mm, height - 28 * mm, f"Gerado em: {datetime.now().strftime('%d/%m/%Y às %H:%M')}")
    p.drawString(margin_left + 40 * mm, height - 35 * mm, f"Total de inspeções: {len(inspections)}")

    # divisor
    p.setStrokeColor(cor_prim)
    p.setLineWidth(1)
    p.line(margin_left, height - 40 * mm, width - margin_right, height - 40 * mm)

    y = height - 50 * mm

    # título do índice
    p.setFillColor(cor_prim)
    p.rect(margin_left, y, content_width, 7 * mm, fill=1)
    p.setFillColor(cor_sec)
    p.setFont("Helvetica-Bold", 9)
    p.drawString(margin_left + 2 * mm, y + 2 * mm, "ÍNDICE DE INSPEÇÕES")
    y -= 15 * mm

    # preparar dados da tabela
    headers = ["Nº", "Data", "Caminhão", "Hodômetro", "Observações"]
    data = [headers]

    for i, insp in enumerate(inspections, start=1):
        # truncar observações para caber na tabela
        obs = (insp.notes[:30] + "...") if insp.notes and len(insp.notes) > 30 else (insp.notes or "—")
        data.append([
            str(i),
            insp.date.strftime("%d/%m/%Y"),
            insp.truck.plate,
            f"{insp.odometer or '—'} km",
            obs
        ])

    # larguras das colunas
    colw = [15*mm, 25*mm, 30*mm, 25*mm, 85*mm]
    if sum(colw) > content_width:
        factor = content_width / sum(colw)
        colw = [w * factor for w in colw]

    # criar tabela
    table = Table(data, colWidths=colw)
    style = [
        ("BACKGROUND", (0,0), (-1,0), cor_sec),
        ("TEXTCOLOR",  (0,0), (-1,0), colors.white),
        ("ALIGN",      (0,0), (3,-1), "CENTER"),  # centralizar as 4 primeiras colunas
        ("ALIGN",      (4,0), (4,-1), "LEFT"),    # alinhar observações à esquerda
        ("VALIGN",     (0,0), (-1,-1), "MIDDLE"),
        ("GRID",       (0,0), (-1,-1), 0.5, colors.grey),
        ("ROWBACKGROUNDS", (0,1),(-1,-1), [colors.white, cor_claro]),
        ("FONTSIZE",   (0,0), (-1,-1), 8),
        ("FONTNAME",   (0,0), (-1,0), "Helvetica-Bold"),
        ("LEFTPADDING",  (0,0),(-1,-1),3),
        ("RIGHTPADDING", (0,0),(-1,-1),3),
        ("TOPPADDING",   (0,0),(-1,-1),4),
        ("BOTTOMPADDING",(0,0),(-1,-1),4),
    ]
    table.setStyle(TableStyle(style))

    # calcular altura da tabela
    row_height = 10 * mm
    total_height = len(data) * row_height

    # verificar se cabe na página
    if y - total_height < margin_bottom:
        p.showPage()
        y = height - margin_top - 10 * mm

    # desenhar tabela
    table.wrapOn(p, content_width, height)
    table.drawOn(p, margin_left, y - total_height)

    # rodapé
    p.setFont("Helvetica", 7)
    p.setFillColor(colors.grey)
    p.drawString(margin_left, margin_bottom - 5 * mm, "CheckUp Pneus - Sistema de Inspeção de Veículos")
    p.drawRightString(width - margin_right, margin_bottom - 5 * mm, f"Página 1")

    p.showPage()
    p.save()
    buffer.seek(0)
    return buffer.getvalue()


def gerar_inspecoes_bulk_pdf(inspections):
    """
    Gera um PDF combinado com:
     1) Página de índice estilizada
     2) Cada inspeção individual, na ordem
    """
    # gerar índice estilizado
    indice_bytes = gerar_indice_pdf(inspections)
    
    # concatenar índice + inspeções individuais
    merger = PdfMerger()
    merger.append(BytesIO(indice_bytes))
    
    for insp in inspections:
        pdf_bytes = gerar_inspecao_pdf(insp)
        merger.append(BytesIO(pdf_bytes))

    # gerar saída final
    out = BytesIO()
    merger.write(out)
    merger.close()
    out.seek(0)
    return out.getvalue()