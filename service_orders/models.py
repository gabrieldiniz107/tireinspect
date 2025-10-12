from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db.models import F, Sum, DecimalField, ExpressionWrapper, Max
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
    vehicle_plate = models.CharField("Placa do veículo", max_length=40, blank=True, default="")
    city = models.CharField("Cidade", max_length=80, blank=True, default="")
    manufacturer = models.CharField("Fabricante", max_length=80, blank=True, default="")
    cep = models.CharField("CEP", max_length=10, blank=True, default="")
    fleet = models.CharField("Frota", max_length=50, blank=True)
    model = models.CharField("Modelo", max_length=80, blank=True)
    # Controle de salvamento: pedidos em rascunho não aparecem nas listagens
    is_draft = models.BooleanField(default=False)

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
        service_total = agg.get("total") or Decimal("0.00")
        observation_total = self.trucks.aggregate(total=Sum("observation_price")).get("total") or Decimal("0.00")
        return service_total + observation_total


class ServiceOrderTruck(models.Model):
    order = models.ForeignKey(ServiceOrder, related_name="trucks", on_delete=models.CASCADE)
    date = models.DateField("Data", default=timezone.now)
    plate = models.CharField("Placa", max_length=40, blank=True, default="")
    fleet = models.CharField("Frota", max_length=50, blank=True, default="")
    observation = models.TextField("Observação", blank=True, default="")
    observation_price = models.DecimalField("Valor da observação", max_digits=10, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    # Novo: numeração sequencial por usuário (começa em 3000)
    # Guardamos também o usuário para permitir unicidade por usuário
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, null=True, blank=True)
    truck_number = models.PositiveIntegerField(null=True, blank=True, db_index=True)

    class Meta:
        ordering = ["id"]
        constraints = [
            models.UniqueConstraint(fields=["created_by", "truck_number"], name="uniq_truck_number_per_user")
        ]

    def __str__(self):
        return self.plate

    def save(self, *args, **kwargs):
        # Vincular created_by a partir da ordem, se não estiver setado
        if not self.created_by and getattr(self, "order_id", None):
            try:
                # Evitar reconsulta se já possui instância
                order_obj = getattr(self, "order", None)
                self.created_by = (order_obj.created_by if order_obj else ServiceOrder.objects.only("created_by").get(id=self.order_id).created_by)
            except Exception:
                pass

        # Atribuir número sequencial por usuário, iniciando em 3000
        if self.truck_number is None and self.created_by_id:
            last = (
                ServiceOrderTruck.objects
                .filter(created_by=self.created_by, truck_number__isnull=False)
                .aggregate(m=Max("truck_number"))
                .get("m")
            )
            self.truck_number = (last + 1) if last is not None else 3000

        super().save(*args, **kwargs)


class ServiceOrderItem(models.Model):
    SERVICE_TYPES = (
        (1, "Alinhamento"),
        (2, "Aperto de tirantes"),
        (3, "Borracharia"),
        (4, "Socorro"),
        (5, "Balanceamento"),
        (6, "Destravamento de tirante"),
        (7, "Destravamento de barra"),
        (8, "Consultoria técnica"),
        (9, "Troca de pivô"),
        (10, "Desempeno de barra"),
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
