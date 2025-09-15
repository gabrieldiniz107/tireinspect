from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("service_orders", "0002_add_type_number_date"),
    ]

    operations = [
        migrations.CreateModel(
            name="ServiceOrderTruck",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False, auto_created=True, verbose_name="ID")),
                ("plate", models.CharField(verbose_name="Placa", max_length=10)),
                ("fleet", models.CharField(verbose_name="Frota", max_length=50, blank=True, default="")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("order", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="trucks", to="service_orders.serviceorder")),
            ],
            options={"ordering": ["id"]},
        ),
    ]

