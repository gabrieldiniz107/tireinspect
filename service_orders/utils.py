from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.colors import Color
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Table, TableStyle
from django.utils import formats
from django.conf import settings
from textwrap import wrap
import os


def gerar_pedido_pdf(order):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # Cores da identidade visual (mais discretas)
    cor_prim = Color(0.95, 0.95, 0.95, 1)  # Cinza muito claro para fundos
    cor_sec = Color(0.22, 0.26, 0.3, 1)    # Azul escuro para textos
    cor_claro = Color(0.98, 0.98, 0.98, 1) # Cinza quase branco
    cor_verde = Color(0, 0.7, 0, 1)        # Verde
    cor_vermelho = Color(0.8, 0, 0, 1)     # Vermelho

    # Margens consistentes
    margin_left = 15 * mm
    margin_right = 15 * mm
    margin_top = 15 * mm
    margin_bottom = 15 * mm
    content_width = width - margin_left - margin_right

    # Dados fixos do cabeçalho
    LOGO_PATH = os.path.join(settings.BASE_DIR, "static", "img", "checkUpPneus_logo.png")
    SIGN_CHECKUP_PATH = os.path.join(settings.BASE_DIR, "static", "img", "assinatura_checkUpPneus.png")
    HEADER_CNPJ = "CNPJ: 50.134.564/0001-95"
    HEADER_WHATS = "WhatsApp: (61) 98282-3080"

    def draw_header():
        nonlocal y
        # Logo e informações da empresa
        if os.path.exists(LOGO_PATH):
            c.drawImage(ImageReader(LOGO_PATH), margin_left, height - 35 * mm, 35 * mm, 17 * mm, mask="auto")

        # Título principal
        c.setFillColor(cor_sec)
        c.setFont("Helvetica-Bold", 16)
        c.drawString(margin_left + 40 * mm, height - 20 * mm, "ORDEM DE SERVIÇO")
        
        # Informações do cabeçalho
        c.setFont("Helvetica", 9)
        c.drawString(margin_left + 40 * mm, height - 28 * mm, HEADER_CNPJ)
        c.drawString(margin_left + 40 * mm, height - 32 * mm, HEADER_WHATS)
        
        # Informações da ordem (sem destaque)
        c.setFont("Helvetica", 10)
        c.drawString(margin_left + 40 * mm, height - 40 * mm, f"Nº do pedido: {order.service_number or '—'}")
        data_fmt = formats.date_format(order.order_date, "DATE_FORMAT") if order.order_date else "—"
        c.drawString(margin_left + 110 * mm, height - 40 * mm, f"Data: {data_fmt}")

        # Linha divisória simples
        c.setStrokeColor(colors.lightgrey)
        c.setLineWidth(1)
        c.line(margin_left, height - 45 * mm, width - margin_right, height - 45 * mm)
        
        # Posicionar y para início do conteúdo
        y = height - 55 * mm

    def draw_section_header(title, y_pos):
        """Desenha um cabeçalho de seção simples"""
        c.setFillColor(cor_prim)
        c.rect(margin_left, y_pos, content_width, 8 * mm, fill=1)
        c.setFillColor(cor_sec)
        c.setFont("Helvetica-Bold", 10)
        c.drawString(margin_left + 3 * mm, y_pos + 2.5 * mm, title)
        return y_pos - 12 * mm

    def format_money(v):
        try:
            n = float(v or 0)
        except Exception:
            n = 0.0
        s = f"{n:,.2f}"
        # US -> pt-BR: 1,234.56 => 1.234,56
        s = s.replace(",", "_").replace(".", ",").replace("_", ".")
        return f"R$ {s}"

    def new_page():
        nonlocal y
        c.showPage()
        draw_header()

    def ensure_space(h):
        nonlocal y
        if y - h < margin_bottom + 20 * mm:
            new_page()

    # Variável global y
    y = 0
    
    # Desenhar cabeçalho inicial
    draw_header()

    # SEÇÃO: Dados do cliente
    ensure_space(25 * mm)
    y = draw_section_header("DADOS DO CLIENTE", y)
    
    c.setFont("Helvetica", 10)
    c.setFillColor(cor_sec)
    
    def draw_client_row(label, value, y_pos):
        c.setFont("Helvetica-Bold", 9)
        c.drawString(margin_left + 3 * mm, y_pos, f"{label}:")
        c.setFont("Helvetica", 9)
        c.drawString(margin_left + 35 * mm, y_pos, value or "—")
        return y_pos - 6 * mm

    y = draw_client_row("Cliente", order.client, y)
    y = draw_client_row("CNPJ/CPF", order.cnpj_cpf, y)
    y -= 5 * mm

    # SEÇÃO: Serviços por caminhão
    ensure_space(20 * mm)
    y = draw_section_header("SERVIÇOS POR CAMINHÃO", y)

    trucks = list(order.trucks.all().prefetch_related("items"))
    
    # Configuração da tabela
    col_widths = [
        content_width * 0.45,  # Serviço - 45%
        content_width * 0.15,  # Qtd - 15%
        content_width * 0.20,  # Preço - 20%
        content_width * 0.20   # Total - 20%
    ]

    # Helper: wrap text to fit a given width using current canvas metrics
    def wrap_text_to_width(text, font_name, font_size, max_width):
        lines = []
        if not (text or "").strip():
            return lines
        words = (text or "").split()
        line = ""
        for w in words:
            test = (line + (" " if line else "") + w)
            if c.stringWidth(test, font_name, font_size) <= max_width:
                line = test
            else:
                if line:
                    lines.append(line)
                # If single word longer than max, hard-break it
                if c.stringWidth(w, font_name, font_size) <= max_width:
                    line = w
                else:
                    curr = ""
                    for ch in w:
                        if c.stringWidth(curr + ch, font_name, font_size) <= max_width:
                            curr += ch
                        else:
                            if curr:
                                lines.append(curr)
                            curr = ch
                    line = curr
        if line:
            lines.append(line)
        return lines

    def draw_services_table(items, truck=None, truck_label=None):
        nonlocal y

        if truck is not None and not truck_label:
            truck_label = f"Placa: {truck.plate}  •  Frota: {truck.fleet or '—'}"

        if truck_label:
            ensure_space(8 * mm)
            # Cabeçalho do caminhão simples (sem emojis nem destaques)
            c.setFillColor(cor_claro)
            c.rect(margin_left, y, content_width, 6 * mm, fill=1)
            c.setFillColor(cor_sec)
            c.setFont("Helvetica-Bold", 9)
            c.drawString(margin_left + 3 * mm, y + 1.5 * mm, truck_label)
            y -= 10 * mm

        subtotal = 0.0

        # Observação do caminhão (fora da tabela), como antes, com quebras corretas
        if truck and (truck.observation or truck.observation_price is not None):
            line_height = 4.8 * mm
            if truck.observation:
                c.setFont("Helvetica-Oblique", 8)
                c.setFillColor(colors.grey)
                max_text_width = content_width - 4 * mm
                # Rótulo
                ensure_space(line_height)
                c.drawString(margin_left + 3 * mm, y, "Observação:")
                y -= line_height
                # Conteúdo, com quebra por largura e página
                lines = wrap_text_to_width(truck.observation, "Helvetica-Oblique", 8, max_text_width)
                for line in lines:
                    ensure_space(line_height)
                    c.drawString(margin_left + 3 * mm, y, line)
                    y -= line_height
            c.setFillColor(cor_sec)
            c.setFont("Helvetica", 8)

        # Se não houver itens nem observação, exibir aviso e sair
        has_obs_row = bool(truck is not None and (truck.observation or truck.observation_price is not None))
        if not items and not has_obs_row:
            ensure_space(6 * mm)
            c.setFont("Helvetica-Oblique", 9)
            c.setFillColor(colors.grey)
            c.drawString(margin_left + 3 * mm, y, "— Nenhum serviço cadastrado")
            y -= 8 * mm
            return subtotal

        # Cabeçalho da tabela
        ensure_space(8 * mm)
        c.setFillColor(cor_sec)
        c.rect(margin_left, y, content_width, 6 * mm, fill=1)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 8)
        
        headers = ["Serviço", "Qtd", "Preço Unit.", "Total"]
        x_pos = margin_left + 2 * mm
        for i, header in enumerate(headers):
            if i == len(headers) - 1:  # Última coluna (Total) alinhada à direita
                c.drawRightString(margin_left + sum(col_widths[:i+1]) - 2 * mm, y + 1.5 * mm, header)
            else:
                c.drawString(x_pos, y + 1.5 * mm, header)
                x_pos += col_widths[i]
        
        y -= 8 * mm

        # Linhas da tabela
        c.setFillColor(cor_sec)
        c.setFont("Helvetica", 8)
        row_index = 0
        # Inserir observação como serviço (com texto longo) se existir
        if has_obs_row:
            try:
                obs_val = float(truck.observation_price) if truck.observation_price is not None else 0.0
            except (TypeError, ValueError):
                obs_val = 0.0

            # Preparar texto completo na primeira coluna
            content_text = (truck.observation or "").strip()
            full_text = ("Observação: " + content_text) if content_text else "Observação"

            # Métricas
            c.setFont("Helvetica", 8)
            c.setFillColor(cor_sec)
            line_h = 4.5 * mm
            pad_y = 1.2 * mm
            pad_x = 2 * mm
            max_text_width = col_widths[0] - (2 * pad_x)

            # Quebra o texto por largura
            lines_all = wrap_text_to_width(full_text, "Helvetica", 8, max_text_width) or ["Observação"]

            # Função para desenhar um "chunk" (parte) que cabe na página atual
            def draw_obs_chunk(lines_chunk, show_values):
                nonlocal y, row_index, subtotal
                rect_h = max(5 * mm, (2 * pad_y) + len(lines_chunk) * line_h)
                # Garantir espaço; se não couber, nova página
                if y - rect_h < margin_bottom + 20 * mm:
                    new_page()
                # Fundo alternado
                c.setFillColor(colors.white if row_index % 2 == 0 else Color(0.97, 0.97, 0.97, 1))
                c.rect(margin_left, y, content_width, rect_h, fill=1)
                c.setFillColor(cor_sec)
                # Texto da primeira coluna (multi-linha, de cima para baixo)
                ty = y + rect_h - pad_y - line_h
                for ln in lines_chunk:
                    c.drawString(margin_left + pad_x, ty + 0.4 * mm, ln)
                    ty -= line_h
                # Outras colunas (apenas no primeiro chunk)
                if show_values:
                    c.drawCentredString(margin_left + col_widths[0] + col_widths[1]/2, y + pad_y, "1")
                    c.drawString(margin_left + col_widths[0] + col_widths[1] + 2 * mm, y + pad_y, format_money(obs_val))
                    c.drawRightString(margin_left + sum(col_widths) - 2 * mm, y + pad_y, format_money(obs_val))
                    subtotal += obs_val
                # Avançar
                y -= (rect_h + 1 * mm)
                row_index += 1

            # Desenhar possivelmente em múltiplas páginas
            lines_remaining = list(lines_all)
            first = True
            while lines_remaining:
                # Quantas linhas cabem na página atual?
                avail_h = y - (margin_bottom + 20 * mm)
                max_fit = int((avail_h - (2 * pad_y)) // line_h) if avail_h > 0 else 0
                if max_fit <= 0:
                    new_page()
                    continue
                n = max_fit if len(lines_remaining) > max_fit else len(lines_remaining)
                chunk = lines_remaining[:n]
                lines_remaining = lines_remaining[n:]
                draw_obs_chunk(chunk, show_values=first)
                first = False

        for item in items:
            ensure_space(6 * mm)
            
            # Alternar cor de fundo das linhas
            c.setFillColor(colors.white if row_index % 2 == 0 else Color(0.97, 0.97, 0.97, 1))
            c.rect(margin_left, y, content_width, 5 * mm, fill=1)
            
            c.setFillColor(cor_sec)
            
            name = item.get_service_type_display()
            qty = item.quantity or 0
            price = item.unit_price or 0
            total = float(price) * float(qty)
            subtotal += total

            # Desenhar dados da linha
            c.drawString(margin_left + 2 * mm, y + 1 * mm, str(name)[:40])  # Truncar se muito longo
            c.drawCentredString(margin_left + col_widths[0] + col_widths[1]/2, y + 1 * mm, str(qty))
            c.drawString(margin_left + col_widths[0] + col_widths[1] + 2 * mm, y + 1 * mm, format_money(price))
            c.drawRightString(margin_left + sum(col_widths) - 2 * mm, y + 1 * mm, format_money(total))
            
            y -= 6 * mm
            row_index += 1

        # Subtotal discreto
        ensure_space(6 * mm)
        c.setFillColor(cor_sec)
        c.setFont("Helvetica", 9)
        c.drawRightString(margin_left + sum(col_widths) - 2 * mm, y, f"Subtotal: {format_money(subtotal)}")
        y -= 10 * mm
        
        return subtotal

    total_geral = 0.0

    if trucks:
        for truck in trucks:
            # Label do caminhão sem emoji e sem destaque especial
            truck_label = f"Placa: {truck.plate}  •  Frota: {truck.fleet or '—'}"
            items = list(truck.items.all())
            subtotal = draw_services_table(items, truck=truck, truck_label=truck_label)
            total_geral += subtotal
    else:
        ensure_space(8 * mm)
        c.setFont("Helvetica-Oblique", 10)
        c.setFillColor(colors.grey)
        c.drawString(margin_left + 3 * mm, y, "— Nenhum caminhão vinculado a esta ordem")
        y -= 10 * mm

    # Serviços sem caminhão (compatibilidade)
    other_items = list(order.items.filter(truck__isnull=True))
    if other_items:
        ensure_space(15 * mm)
        y = draw_section_header("SERVIÇOS ADICIONAIS", y)
        subtotal = draw_services_table(other_items)
        total_geral += subtotal

    # Total geral discreto no canto direito
    ensure_space(10 * mm)
    c.setStrokeColor(colors.lightgrey)
    c.setLineWidth(0.5)
    c.line(margin_left + content_width * 0.65, y, width - margin_right, y)
    y -= 8 * mm
    
    # Total pequeno e alinhado à direita
    c.setFillColor(cor_sec)
    c.setFont("Helvetica-Bold", 10)
    c.drawRightString(width - margin_right, y, f"Total Geral: {format_money(order.total_amount)}")
    y -= 10 * mm

    # SEÇÃO: Assinaturas (sem título e sem caixas)
    ensure_space(35 * mm)

    # Layout lado a lado
    gap = 8 * mm
    col_w = (content_width - gap) / 2
    x_left = margin_left
    x_right = margin_left + col_w + gap

    # Área para a imagem da CheckUp acima da linha
    img_area_h = 22 * mm
    line_offset = 2 * mm  # espaço entre a área e a linha

    # Desenhar imagem de assinatura da CheckUp Pneus (opcional)
    if os.path.exists(SIGN_CHECKUP_PATH):
        try:
            img = ImageReader(SIGN_CHECKUP_PATH)
            img_w, img_h = img.getSize()
            pad = 3 * mm
            max_w = col_w - 2 * pad
            max_h = img_area_h - 2 * pad
            scale = min(max_w / img_w, max_h / img_h)
            draw_w = img_w * scale
            draw_h = img_h * scale
            draw_x = x_left + (col_w - draw_w) / 2
            draw_y = y - img_area_h + (img_area_h - draw_h) / 2
            c.drawImage(img, draw_x, draw_y, draw_w, draw_h, mask="auto")
        except Exception:
            pass

    # Linhas de assinatura acima dos nomes
    c.setStrokeColor(colors.lightgrey)
    c.setLineWidth(0.8)
    line_y = y - img_area_h - line_offset
    c.line(x_left, line_y, x_left + col_w, line_y)     # linha CheckUp
    c.line(x_right, line_y, x_right + col_w, line_y)   # linha Cliente

    # Nomes abaixo das linhas
    c.setFillColor(cor_sec)
    c.setFont("Helvetica", 9)
    label_y = line_y - 4 * mm
    c.drawCentredString(x_left + col_w / 2, label_y, "CheckUp Pneus")
    c.drawCentredString(x_right + col_w / 2, label_y, "Cliente")
    y = label_y - 8 * mm

    # Rodapé
    c.setFont("Helvetica", 7)
    c.setFillColor(colors.grey)
    c.drawString(margin_left, margin_bottom - 5 * mm, "CheckUp Pneus - Sistema de Gestão de Serviços")
    c.drawRightString(width - margin_right, margin_bottom - 5 * mm, "Gerado por TireInspect")

    c.showPage()
    c.save()
    pdf = buffer.getvalue()
    buffer.close()
    return pdf
