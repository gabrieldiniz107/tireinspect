from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("service_orders", "0005_serviceorderitem"),
    ]

    operations = [
        migrations.AddField(
            model_name="serviceorderitem",
            name="truck",
            field=models.ForeignKey(
                to="service_orders.serviceordertruck",
                on_delete=django.db.models.deletion.CASCADE,
                related_name="items",
                null=True,
                blank=True,
            ),
        ),
    ]
