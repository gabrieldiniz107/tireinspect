from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db.models import F, Sum, DecimalField, ExpressionWrapper
from decimal import Decimal
from core.models import Company

User = get_user_model()


class ServiceOrder(models.Model):
    """
    Pedido de serviço preenchido pelo usuário.
    Campos principais conforme solicitado.
    """

    # Quem criou (para filtrar por usuário)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)

    # Campos do formulário
    ORDER_TYPE_CHOICES = (
        ("orcamento", "Orçamento"),
        ("servico", "Serviço"),
    )

    order_type = models.CharField("Tipo", max_length=10, choices=ORDER_TYPE_CHOICES, default="servico")
    service_number = models.CharField("Número do serviço", max_length=30, default="")
    order_date = models.DateField("Data", default=timezone.now)
    # Vincula a uma empresa cadastrada (opcional, permite pedidos avulsos)
    company = models.ForeignKey(Company, related_name="service_orders", on_delete=models.SET_NULL, null=True, blank=True)
    client = models.CharField("Cliente", max_length=120)
    cnpj_cpf = models.CharField("CNPJ/CPF", max_length=20)
    vehicle_plate = models.CharField("Placa do veículo", max_length=10, blank=True, default="")
    city = models.CharField("Cidade", max_length=80, blank=True, default="")
    manufacturer = models.CharField("Fabricante", max_length=80, blank=True, default="")
    cep = models.CharField("CEP", max_length=10, blank=True, default="")
    fleet = models.CharField("Frota", max_length=50, blank=True)
    model = models.CharField("Modelo", max_length=80, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return f"{self.client} - {self.vehicle_plate}"

    @property
    def total_amount(self):
        expr = ExpressionWrapper(F("quantity") * F("unit_price"), output_field=DecimalField(max_digits=12, decimal_places=2))
        agg = self.items.aggregate(total=Sum(expr))
        return agg.get("total") or Decimal("0.00")


class ServiceOrderTruck(models.Model):
    order = models.ForeignKey(ServiceOrder, related_name="trucks", on_delete=models.CASCADE)
    plate = models.CharField("Placa", max_length=10)
    fleet = models.CharField("Frota", max_length=50, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return self.plate


class ServiceOrderItem(models.Model):
    SERVICE_TYPES = (
        (1, "Alinhamento"),
        (2, "Aperto de tirantes"),
        (3, "Borracharia"),
        (4, "Socorro"),
        (5, "Balanceamento"),
    )

    order = models.ForeignKey(ServiceOrder, related_name="items", on_delete=models.CASCADE)
    # Novo: item associado a um caminhão específico (opcional para compatibilidade)
    truck = models.ForeignKey('ServiceOrderTruck', related_name='items', on_delete=models.CASCADE, null=True, blank=True)
    service_type = models.PositiveSmallIntegerField(choices=SERVICE_TYPES)
    quantity = models.PositiveIntegerField(default=0)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"{self.get_service_type_display()} x{self.quantity}"

    @property
    def total_price(self):
        return (self.unit_price or Decimal("0")) * Decimal(self.quantity or 0)
