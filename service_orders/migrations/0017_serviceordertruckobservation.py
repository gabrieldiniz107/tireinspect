from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("service_orders", "0016_alter_serviceorder_vehicle_plate_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="ServiceOrderTruckObservation",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("content", models.TextField(blank=True, default="", verbose_name="Observação")),
                ("price", models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name="Valor da observação")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "truck",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="observations", to="service_orders.serviceordertruck"),
                ),
            ],
            options={
                "ordering": ["id"],
            },
        ),
    ]

