from django.urls import path
from . import views

app_name = "service_orders"

urlpatterns = [
    path("", views.order_list, name="order_list"),
    path("novo/", views.order_create, name="order_create"),
    path("novo/dados/", views.order_create_step2, name="order_create_step2"),
    path("novo/servicos/<int:order_id>/", views.order_create_step3, name="order_create_step3"),
    # Edit flow
    path("editar/<int:order_id>/", views.order_edit_step1, name="order_edit_step1"),
    path("editar/dados/<int:order_id>/", views.order_edit_step2, name="order_edit_step2"),
    path("editar/servicos/<int:order_id>/", views.order_edit_step3, name="order_edit_step3"),
    path("<int:order_id>/", views.order_detail, name="order_detail"),
    path("<int:order_id>/pdf/", views.order_pdf, name="order_pdf"),
    path("<int:order_id>/excluir/", views.order_delete, name="order_delete"),
]
