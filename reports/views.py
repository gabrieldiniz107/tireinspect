from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required

from core.models import Inspection
from .utils import gerar_inspecao_pdf

@login_required
def inspection_pdf(request, inspection_id):
    inspecao = get_object_or_404(
        Inspection,
        pk=inspection_id,
        truck__company__created_by=request.user
    )
    pdf_bytes = gerar_inspecao_pdf(inspecao)
    response = HttpResponse(pdf_bytes, content_type="application/pdf")
    response["Content-Disposition"] = f"attachment; filename=inspecao_{inspection_id}.pdf"
    return response
