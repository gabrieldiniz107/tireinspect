from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

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


class ServiceOrderTruck(models.Model):
    order = models.ForeignKey(ServiceOrder, related_name="trucks", on_delete=models.CASCADE)
    plate = models.CharField("Placa", max_length=10)
    fleet = models.CharField("Frota", max_length=50, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return self.plate
