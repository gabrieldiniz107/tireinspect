from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("service_orders", "0004_relax_required_fields"),
    ]

    operations = [
        migrations.CreateModel(
            name="ServiceOrderItem",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False, auto_created=True, verbose_name="ID")),
                ("service_type", models.PositiveSmallIntegerField(choices=[
                    (1, "Alinhamento"),
                    (2, "Aperto de tirantes"),
                    (3, "Borracharia"),
                    (4, "Socorro"),
                    (5, "Balanceamento"),
                ])),
                ("quantity", models.PositiveIntegerField(default=0)),
                ("unit_price", models.DecimalField(max_digits=10, decimal_places=2, default=0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("order", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="items", to="service_orders.serviceorder")),
            ],
            options={"ordering": ["id"]},
        ),
    ]

