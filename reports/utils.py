from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.lib.colors import Color
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors
import os
from reportlab.lib.utils import ImageReader


def gerar_inspecao_pdf(inspecao):
    """
    Gera PDF de inspeção:
    - 1ª página: logo, dados, tabela de pneus e (se axes<3) imagem inline.
    - Se eixos>=3: adiciona 2ª página com imagem full-page.
    """
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # cores
    cor_prim = Color(1, 0.82, 0, 1)
    cor_sec = Color(0.22, 0.26, 0.3, 1)
    cor_claro = Color(0.9, 0.9, 0.9, 1)

    # cabeçalho logo
    logo = os.path.join('static', 'img', 'checkUpPneus_logo.png')
    if os.path.exists(logo):
        p.drawImage(ImageReader(logo), 20*mm, height-30*mm, 40*mm, 20*mm, mask='auto')

    # título
    p.setFillColor(cor_sec)
    p.setFont('Helvetica-Bold', 16)
    p.drawString(70*mm, height-20*mm, 'INSPEÇÃO DE VEÍCULO')
    p.setFont('Helvetica-Bold', 12)
    p.drawString(70*mm, height-28*mm, f'Caminhão: {inspecao.truck.plate}')

    # dados gerais
    p.setFont('Helvetica', 10)
    p.drawString(70*mm, height-35*mm, f'Data: {inspecao.date.strftime("%d/%m/%Y")}')
    p.drawString(110*mm, height-35*mm, f'Hodômetro: {inspecao.odometer} km')

    # linha
    p.setStrokeColor(cor_prim)
    p.setLineWidth(1)
    p.line(20*mm, height-40*mm, width-20*mm, height-40*mm)

    # conteúdo inicia aqui
    y = height-50*mm

    # seção dados inspeção
    p.setFillColor(cor_prim)
    p.rect(20*mm, y, width-40*mm, 8*mm, fill=1)
    p.setFillColor(cor_sec)
    p.setFont('Helvetica-Bold', 10)
    p.drawString(22*mm, y+2.5*mm, 'DADOS DA INSPEÇÃO')
    y -= 15*mm
    p.setFont('Helvetica', 9)
    if inspecao.notes:
        p.drawString(22*mm, y, f'Observações: {inspecao.notes}')
        y -= 5*mm

    # tabela pneus
    y -= 10*mm
    p.setFillColor(cor_prim)
    p.rect(20*mm, y, width-40*mm, 8*mm, fill=1)
    p.setFillColor(cor_sec)
    p.setFont('Helvetica-Bold', 10)
    p.drawString(22*mm, y+2.5*mm, 'RELATÓRIO DE PNEUS')
    y -= 10*mm

    headers = ['Pos','Sulcos','Marca','Desenho','Nº Fogo','DOT','Recap']
    data = [headers]
    for t in inspecao.tires.all():
        sc = f"{t.groove_1}/{t.groove_2}/{t.groove_3}/{t.groove_4}"
        data.append([str(t.position), sc, t.brand or '—', t.pattern or '—',
                     t.fire_number or '—', t.dot or '—', 'Sim' if t.rec else 'Não'])
    colw = [15*mm,25*mm,25*mm,25*mm,25*mm,25*mm,20*mm]
    table = Table(data, colWidths=colw)
    table.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0),cor_sec),
        ('TEXTCOLOR',(0,0),(-1,0),colors.white),
        ('ALIGN',(0,0),(-1,-1),'CENTER'),
        ('GRID',(0,0),(-1,-1),0.5,colors.grey),
        ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,cor_claro])
    ]))
    table.wrapOn(p,width,height)
    th = len(data)*8*mm
    table.drawOn(p,20*mm,y-th)
    y -= (th+15*mm)

    # preparar imagem
    tt = inspecao.truck.truck_type
    imgf = f'ca-{tt.axle_count}eixos_{tt.tire_count}pneus.png'
    imgp = os.path.join('static','img',imgf)
    label = f"{tt.axle_count} eixos e {tt.tire_count} pneus"

    # se >=3 eixos: nova página full image
    if tt.axle_count>=3 and os.path.exists(imgp):
        p.showPage()
        p.drawImage(ImageReader(imgp), 0,0, width=width, height=height, mask='auto')
    else:
        # inline na 1ª página:
        # label
        p.setFont('Helvetica-Bold',12)
        p.setFillColor(cor_sec)
        lw = p.stringWidth(label,'Helvetica-Bold',12)
        p.drawString((width-lw)/2, y+3*mm, label)
        # imagem menor centralizada
        if os.path.exists(imgp):
            iw, ih = 100*mm,100*mm
            x = (width-iw)/2
            p.drawImage(ImageReader(imgp), x, y-ih, width=iw, height=ih, mask='auto')

    # rodapé página atual
    p.setStrokeColor(cor_sec)
    p.setLineWidth(0.5)
    p.line(20*mm,15*mm+5*mm,width-20*mm,15*mm+5*mm)
    p.setFont('Helvetica',8)
    p.setFillColor(cor_sec)
    p.drawString(20*mm,15*mm, f"Inspeção #{inspecao.id} • {inspecao.date.strftime('%d/%m/%Y')}")
    p.drawRightString(width-20*mm,15*mm, str(p.getPageNumber()))

    p.showPage()
    p.save()
    buffer.seek(0)
    return buffer.getvalue()
