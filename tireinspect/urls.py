# tireinspect/urls.py
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/login/", auth_views.LoginView.as_view(template_name="core/login.html"), name="login"),
    path("", include("core.urls")),
    path("reports/", include("reports.urls", namespace="reports")),
    path(
       "relatorios/",
        include(("inspection_reports.urls", "inspection_reports"), namespace="inspection_reports"),
     ),
    path("pedidos/", include("service_orders.urls", namespace="service_orders")),

]
