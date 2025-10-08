from django import forms
from django.forms import modelformset_factory, inlineformset_factory
from django.forms.models import BaseInlineFormSet
from .models import ServiceOrder, ServiceOrderTruck, ServiceOrderItem
from core.models import Company


class ServiceOrderForm(forms.ModelForm):
    class Meta:
        model = ServiceOrder
        fields = [
            "company",
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
            "cnpj_cpf": forms.TextInput(
                attrs={
                    "data-mask-cnpj": "true",
                    "placeholder": "00.000.000/0000-00",
                    "maxlength": "18",
                    "inputmode": "numeric",
                    "autocomplete": "off",
                }
            ),
        }
        labels = {
            "cnpj_cpf": "CNPJ",
        }


class ServiceOrderStep1Form(forms.ModelForm):
    class Meta:
        model = ServiceOrder
        fields = ["order_date"]
        widgets = {
            "order_date": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        from django.utils import timezone
        super().__init__(*args, **kwargs)
        # Define a data atual como padrão (form não vinculado e sem instance nova)
        if not self.is_bound:
            has_instance = hasattr(self, "instance") and getattr(self.instance, "pk", None)
            if not has_instance and not self.initial.get("order_date"):
                today = timezone.localdate()
                self.initial["order_date"] = today
                self.fields["order_date"].initial = today


class ServiceOrderStep2Form(forms.ModelForm):
    truck_count = forms.IntegerField(label="Quantidade de caminhões", min_value=1, max_value=10, initial=1)

    class Meta:
        model = ServiceOrder
        fields = ["company", "client", "cnpj_cpf"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # queryset será definido na view para filtrar por usuário logado
        self.fields["company"].queryset = Company.objects.none()
        self.fields["company"].required = False
        self.fields["client"].required = False
        self.fields["cnpj_cpf"].label = "CNPJ"
        self.fields["cnpj_cpf"].required = False
        self.fields["cnpj_cpf"].widget.attrs.update(
            {
                "data-mask-cnpj": "true",
                "placeholder": "00.000.000/0000-00",
                "maxlength": "18",
                "inputmode": "numeric",
                "autocomplete": "off",
            }
        )


class ServiceOrderTruckForm(forms.ModelForm):
    class Meta:
        model = ServiceOrderTruck
        fields = ["plate", "fleet", "observation", "observation_price"]
        widgets = {
            "observation": forms.Textarea(
                attrs={
                    "rows": 2,
                    "class": "w-full",
                    "placeholder": "Descreva a observação deste caminhão",
                }
            ),
            "observation_price": forms.NumberInput(
                attrs={
                    "step": "0.01",
                    "min": "0",
                    "class": "w-full",
                    "placeholder": "0,00",
                }
            ),
        }


TruckFormSet = modelformset_factory(
    ServiceOrderTruck,
    form=ServiceOrderTruckForm,
    extra=10,
    max_num=10,
    validate_max=True,
    can_delete=False,
)


class ServiceItemsForm(forms.Form):
    number_widget = forms.NumberInput(attrs={"step": 1, "min": 0})
    money_widget = forms.NumberInput(attrs={"step": "0.01", "min": 0})

    alinhamento_qty = forms.IntegerField(label="Alinhamento - quantidade", min_value=0, initial=0, widget=number_widget)
    alinhamento_price = forms.DecimalField(label="Alinhamento - preço unitário", min_value=0, max_digits=10, decimal_places=2, initial=0, widget=money_widget)

    tirantes_qty = forms.IntegerField(label="Aperto de tirantes - quantidade", min_value=0, initial=0, widget=number_widget)
    tirantes_price = forms.DecimalField(label="Aperto de tirantes - preço unitário", min_value=0, max_digits=10, decimal_places=2, initial=0, widget=money_widget)

    borracharia_qty = forms.IntegerField(label="Borracharia - quantidade", min_value=0, initial=0, widget=number_widget)
    borracharia_price = forms.DecimalField(label="Borracharia - preço unitário", min_value=0, max_digits=10, decimal_places=2, initial=0, widget=money_widget)

    socorro_qty = forms.IntegerField(label="Socorro - quantidade", min_value=0, initial=0, widget=number_widget)
    socorro_price = forms.DecimalField(label="Socorro - preço unitário", min_value=0, max_digits=10, decimal_places=2, initial=0, widget=money_widget)

    balanceamento_qty = forms.IntegerField(label="Balanceamento - quantidade", min_value=0, initial=0, widget=number_widget)
    balanceamento_price = forms.DecimalField(label="Balanceamento - preço unitário", min_value=0, max_digits=10, decimal_places=2, initial=0, widget=money_widget)


class ServiceOrderItemForm(forms.ModelForm):
    class Meta:
        model = ServiceOrderItem
        fields = ["service_type", "quantity", "unit_price"]
        widgets = {
            "service_type": forms.Select(attrs={"class": "w-full"}),
            "quantity": forms.NumberInput(attrs={"min": 0, "step": 1, "inputmode": "numeric", "class": "w-full"}),
            "unit_price": forms.NumberInput(attrs={"min": 0, "step": "0.01", "inputmode": "decimal", "class": "w-full"}),
        }


TruckItemFormSet = inlineformset_factory(
    parent_model=ServiceOrderTruck,
    model=ServiceOrderItem,
    form=ServiceOrderItemForm,
    extra=1,
    can_delete=True,
    fields=["service_type", "quantity", "unit_price"],
)


class TruckItemBaseFormSet(BaseInlineFormSet):
    def save_new(self, form, commit=True):
        obj = super().save_new(form, commit=False)
        # Ensure 'order' is set based on parent truck
        if obj.order_id is None:
            obj.order = self.instance.order
        if commit:
            obj.save()
            form.save_m2m()
        return obj

    def save_existing(self, form, instance, commit=True):
        obj = super().save_existing(form, instance, commit=False)
        if obj.order_id is None:
            obj.order = self.instance.order
        if commit:
            obj.save()
            form.save_m2m()
        return obj

# Rebuild formset with custom base to enforce order
TruckItemFormSet = inlineformset_factory(
    parent_model=ServiceOrderTruck,
    model=ServiceOrderItem,
    form=ServiceOrderItemForm,
    formset=TruckItemBaseFormSet,
    extra=1,
    can_delete=True,
    fields=["service_type", "quantity", "unit_price"],
)
