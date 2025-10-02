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
        widgets = {
            "cnpj": forms.TextInput(
                attrs={
                    "data-mask-cnpj": "true",
                    "placeholder": "00.000.000/0000-00",
                    "maxlength": "18",
                    "inputmode": "numeric",
                    "autocomplete": "off",
                }
            )
        }

class TruckForm(forms.ModelForm):
    class Meta:
        model = Truck
        fields = ["truck_type", "plate", "fleet", "brand", "model", "hodometer"]


class TruckEditForm(forms.ModelForm):
    class Meta:
        model = Truck
        # Editáveis: placa, marca, modelo e frota (tipo permanece bloqueado)
        fields = ["plate", "brand", "model", "fleet"]

class InspectionForm(forms.ModelForm):
    class Meta:
        model = Inspection
        fields = ["date", "odometer", "notes"]

class TireForm(forms.ModelForm):
    # Adicionar campo de escolha para recapagem com opções Sim/Não
    rec = forms.ChoiceField(
        label="Novo",
        choices=((True, "Sim"), (False, "Não")),
        widget=forms.RadioSelect,
        initial=False
    )
    
    class Meta:
        model = Tire
        exclude = ("inspection", "position")  # definiremos no view
        
    def __init__(self, *args, **kwargs):
        super(TireForm, self).__init__(*args, **kwargs)
        # Se o objeto já existe, converte o valor booleano em string para o campo
        if self.instance.pk and 'rec' in self.initial:
            self.initial['rec'] = str(self.initial['rec']).lower() == 'true'
            
    def clean_rec(self):
        # Converter a string 'True'/'False' para o valor booleano correspondente
        value = self.cleaned_data['rec']
        if isinstance(value, str):
            return value == 'True'
        return value   # definiremos no view

# Formset dinâmico – vamos instanciar com extra=tire_count no view
TireFormSet = inlineformset_factory(
    Inspection, Tire, form=TireForm,
    extra=0, can_delete=False
)
