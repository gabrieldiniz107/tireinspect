from django.urls import path
from . import views

app_name = "reports"

urlpatterns = [
    path("inspecao/<int:inspection_id>/pdf/", views.inspection_pdf, name="inspection_pdf",),
    # ... suas outras URLs existentes ...
    path('inspection/<int:inspection_id>/pdf/', views.inspection_pdf, name='inspection_pdf'),
    path('bulk-pdf/', views.bulk_inspection_pdf, name='bulk_inspection_pdf'),
    # ... outras URLs ...

    
]
