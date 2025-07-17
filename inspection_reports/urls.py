# inspection_reports/urls.py
from django.urls import path
from inspection_reports.views import report_by_month_range  # import explícito

app_name = "inspection_reports"

urlpatterns = [
    path("intervalo/meses/", report_by_month_range, name="report_by_month"),
]
