from django.db import models
from django.contrib.auth import get_user_model
from datetime import date

User = get_user_model()

class Company(models.Model):
    """Empresa dona dos caminhões."""
    name       = models.CharField("Empresa", max_length=120)
    cnpj       = models.CharField("CNPJ", max_length=18, blank=True)
    contact    = models.CharField("Contato", max_length=120, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class TruckType(models.Model):
    """Template fixo – 8 combinações de eixos e pneus."""
    code         = models.CharField(max_length=50, unique=True)
    description  = models.CharField(max_length=60)
    axle_count   = models.PositiveSmallIntegerField()
    tire_count   = models.PositiveSmallIntegerField()

    class Meta:
        ordering = ["axle_count", "tire_count"]

    def __str__(self):
        return f"{self.description} – {self.axle_count} eixos / {self.tire_count} pneus"


class Truck(models.Model):
    """Caminhão específico de uma empresa."""
    company     = models.ForeignKey(Company, related_name="trucks",
                                    on_delete=models.CASCADE)
    truck_type  = models.ForeignKey(TruckType, on_delete=models.PROTECT)
    plate       = models.CharField("Placa", max_length=10)
    fleet       = models.CharField("Frota", max_length=50, blank=True, default="")
    brand       = models.CharField("Marca", max_length=50, blank=True)
    model       = models.CharField("Modelo", max_length=50, blank=True)
    hodometer   = models.PositiveIntegerField("Hodômetro", null=True, blank=True)

    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [("company", "plate")]
        ordering = ["plate"]

    def __str__(self):
        return self.plate

# …Company, TruckType, Truck já existem

class Inspection(models.Model):
    """
    Uma inspeção (fotografia) de todos os pneus de um caminhão
    em determinada data.
    """
    truck       = models.ForeignKey("Truck", related_name="inspections",
                                    on_delete=models.CASCADE)
    date        = models.DateField(default=date.today)
    odometer    = models.PositiveIntegerField("Hodômetro", null=True, blank=True)
    notes       = models.TextField("Observações", blank=True)

    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date", "-id"]

    def __str__(self):
        return f"{self.truck.plate} – {self.date}"



class Tire(models.Model):
    """
    Dados individuais de um pneu naquela inspeção.
    position: 1 … tire_count do TruckType (para PDF/diagramas futuros)
    """
    inspection  = models.ForeignKey(Inspection, related_name="tires",
                                    on_delete=models.CASCADE)
    position    = models.PositiveSmallIntegerField()
    # 4 sulcos (profundidade em mm – mas deixe livre por enquanto)
    groove_1    = models.CharField("Sulco D", max_length=10, blank=True)
    groove_2    = models.CharField("Sulco M", max_length=10, blank=True)
    groove_3    = models.CharField("Sulco F", max_length=10, blank=True)
    brand       = models.CharField("Marca", max_length=30, blank=True)
    pattern     = models.CharField("Desenho", max_length=30, blank=True)
    fire_number = models.CharField("Nº Fogo", max_length=20, blank=True)
    dot         = models.CharField("DOT", max_length=15, blank=True)
    rec         = models.BooleanField("Recapado", default=False)

    class Meta:
        unique_together = [("inspection", "position")]
        ordering = ["position"]

    def __str__(self):
        return f"Pneu {self.position}"
