from django.urls import path
from . import views

app_name = "service_orders"

urlpatterns = [
    path("", views.order_list, name="order_list"),
    path("novo/", views.order_create, name="order_create"),
    path("novo/dados/", views.order_create_step2, name="order_create_step2"),
    path("<int:order_id>/", views.order_detail, name="order_detail"),
    path("<int:order_id>/pdf/", views.order_pdf, name="order_pdf"),
]
