from django import forms
from django.forms import modelformset_factory
from .models import ServiceOrder, ServiceOrderTruck


class ServiceOrderForm(forms.ModelForm):
    class Meta:
        model = ServiceOrder
        fields = [
            "service_number",
            "order_date",
            "client",
            "cnpj_cpf",
            "vehicle_plate",
            "city",
            "manufacturer",
            "cep",
            "fleet",
            "model",
        ]

        widgets = {
            "order_date": forms.DateInput(attrs={"type": "date"}),
        }


class ServiceOrderStep1Form(forms.ModelForm):
    class Meta:
        model = ServiceOrder
        fields = ["service_number", "order_date"]
        widgets = {
            "order_date": forms.DateInput(attrs={"type": "date"}),
        }


class ServiceOrderStep2Form(forms.ModelForm):
    truck_count = forms.IntegerField(label="Quantidade de caminhões", min_value=1, max_value=10, initial=1)

    class Meta:
        model = ServiceOrder
        fields = ["client", "cnpj_cpf"]


class ServiceOrderTruckForm(forms.ModelForm):
    class Meta:
        model = ServiceOrderTruck
        fields = ["plate", "fleet"]


TruckFormSet = modelformset_factory(
    ServiceOrderTruck,
    form=ServiceOrderTruckForm,
    extra=10,
    max_num=10,
    validate_max=True,
    can_delete=False,
)
