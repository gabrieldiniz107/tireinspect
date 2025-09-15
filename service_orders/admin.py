from django.contrib import admin
from .models import ServiceOrder


@admin.register(ServiceOrder)
class ServiceOrderAdmin(admin.ModelAdmin):
    list_display = ("client", "vehicle_plate", "city", "manufacturer", "created_at")
    search_fields = ("client", "cnpj_cpf", "vehicle_plate", "city", "manufacturer", "fleet", "model")
    list_filter = ("manufacturer", "city")

