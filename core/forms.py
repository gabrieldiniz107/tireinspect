# core/forms.py
from django import forms
from .models import Company, Truck, Inspection, Tire
from django.forms import inlineformset_factory
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model

User = get_user_model()

class UserRegisterForm(UserCreationForm):
    email = forms.EmailField(label="E‑mail")

    class Meta:
        model  = User
        fields = ("username", "email", "password1", "password2")


class CompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = ["name", "cnpj", "contact"]

class TruckForm(forms.ModelForm):
    class Meta:
        model = Truck
        fields = ["truck_type", "plate", "brand", "model", "hodometer"]

class InspectionForm(forms.ModelForm):
    class Meta:
        model = Inspection
        fields = ["date", "odometer", "notes"]

class TireForm(forms.ModelForm):
    class Meta:
        model = Tire
        exclude = ("inspection", "position")   # definiremos no view

# Formset dinâmico – vamos instanciar com extra=tire_count no view
TireFormSet = inlineformset_factory(
    Inspection, Tire, form=TireForm,
    extra=0, can_delete=False
)