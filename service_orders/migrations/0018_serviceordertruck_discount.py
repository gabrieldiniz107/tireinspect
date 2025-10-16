from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("service_orders", "0017_serviceordertruckobservation"),
    ]

    operations = [
        migrations.AddField(
            model_name="serviceordertruck",
            name="discount",
            field=models.DecimalField(null=True, blank=True, max_digits=10, decimal_places=2, verbose_name="Desconto"),
        ),
    ]

