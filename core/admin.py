from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group

from .models import Company, TruckType, Truck, Tire, Inspection

User = get_user_model()


# Cadastro de usuários no admin


# Registro dos outros modelos
@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ("name", "cnpj", "created_by", "created_at")
    search_fields = ("name", "cnpj")


@admin.register(Truck)
class TruckAdmin(admin.ModelAdmin):
    list_display = ("plate", "company", "truck_type")
    search_fields = ("plate", "company__name")


admin.site.register(TruckType)


@admin.register(Inspection)
class InspectionAdmin(admin.ModelAdmin):
    list_display = ("truck", "date", "odometer")
    date_hierarchy = "date"
    list_filter = ("truck",)


@admin.register(Tire)
class TireAdmin(admin.ModelAdmin):
    list_display = ("inspection", "position", "brand", "dot", "rec")
    list_filter = ("inspection__truck", "rec")
    search_fields = ("brand", "dot")
