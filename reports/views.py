from django.shortcuts import get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
import json

from core.models import Inspection
from .utils import gerar_inspecao_pdf, gerar_inspecoes_bulk_pdf

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

@login_required
@require_POST
def bulk_inspection_pdf(request):
    try:
        # Pegar os IDs das inspeções selecionadas
        data = json.loads(request.body)
        inspection_ids = data.get('inspection_ids', [])
        
        if not inspection_ids:
            return JsonResponse({'error': 'Nenhuma inspeção selecionada'}, status=400)
        
        # Verificar se todas as inspeções pertencem ao usuário
        inspections = Inspection.objects.filter(
            pk__in=inspection_ids,
            truck__company__created_by=request.user
        ).select_related('truck', 'truck__company').order_by('-date')
        
        if not inspections.exists():
            return JsonResponse({'error': 'Nenhuma inspeção válida encontrada'}, status=400)
        
        # Gerar PDF combinado
        pdf_bytes = gerar_inspecoes_bulk_pdf(inspections)
        
        response = HttpResponse(pdf_bytes, content_type="application/pdf")
        response["Content-Disposition"] = f"attachment; filename=inspecoes_combinadas.pdf"
        return response
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Dados inválidos'}, status=400)
    except Exception as e:
        return JsonResponse({'error': 'Erro ao gerar PDF'}, status=500)