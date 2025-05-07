# core/admin.py
from django.contrib import admin
from .models import Company, TruckType, Truck, Tire, Inspection

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ("name", "cnpj", "created_by", "created_at")

@admin.register(Truck)
class TruckAdmin(admin.ModelAdmin):
    list_display = ("plate", "company", "truck_type")

admin.site.register(TruckType)


@admin.register(Inspection)
class InspectionAdmin(admin.ModelAdmin):
    list_display = ("truck", "date", "odometer")
    date_hierarchy = "date"

@admin.register(Tire)
class TireAdmin(admin.ModelAdmin):
    list_display = ("inspection", "position", "brand", "dot")
    list_filter = ("inspection__truck",)
