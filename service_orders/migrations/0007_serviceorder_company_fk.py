from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("service_orders", "0006_serviceorderitem_truck_fk"),
        ("core", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="serviceorder",
            name="company",
            field=models.ForeignKey(
                to="core.company",
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="service_orders",
                null=True,
                blank=True,
            ),
        ),
    ]

