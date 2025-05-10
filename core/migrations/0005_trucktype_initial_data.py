# core/migrations/0002_trucktype_initial_data.py
from django.db import migrations

def add_truck_types(apps, schema_editor):
    TruckType = apps.get_model("core", "TruckType")
    data = [
        ("T12-4E", "Caminhão 4 eixos / 12 pneus", 4, 12),
        ("T12-3E", "Caminhão 3 eixos / 12 pneus", 3, 12),
        ("T16-4E", "Caminhão 4 eixos / 16 pneus", 4, 16),
        ("T08-2E", "Caminhão 2 eixos / 8 pneus", 2, 8),
        ("T06-2E", "Caminhão 2 eixos / 6 pneus", 2, 6),
        ("T10-3E", "Caminhão 3 eixos / 10 pneus", 3, 10),
        ("T08-3E", "Caminhão 3 eixos / 8 pneus", 3, 8),
        ("T10-4E", "Caminhão 4 eixos / 10 pneus", 4, 10),
    ]
    for code, desc, ax, tires in data:
        TruckType.objects.get_or_create(
            code=code,
            defaults={
                "description": desc,
                "axle_count": ax,
                "tire_count": tires,
            },
        )

class Migration(migrations.Migration):

    dependencies = [("core", "0004_alter_code_length")]

    operations = [migrations.RunPython(add_truck_types)]
