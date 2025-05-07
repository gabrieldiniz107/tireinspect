from django.urls import path
from . import views

app_name = "reports"

urlpatterns = [
    path("inspecao/<int:inspection_id>/pdf/", views.inspection_pdf, name="inspection_pdf",)
]
