from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("service_orders", "0003_serviceordertruck"),
    ]

    operations = [
        migrations.AlterField(
            model_name="serviceorder",
            name="vehicle_plate",
            field=models.CharField(verbose_name="Placa do veículo", max_length=10, blank=True, default=""),
        ),
        migrations.AlterField(
            model_name="serviceorder",
            name="city",
            field=models.CharField(verbose_name="Cidade", max_length=80, blank=True, default=""),
        ),
        migrations.AlterField(
            model_name="serviceorder",
            name="manufacturer",
            field=models.CharField(verbose_name="Fabricante", max_length=80, blank=True, default=""),
        ),
        migrations.AlterField(
            model_name="serviceorder",
            name="cep",
            field=models.CharField(verbose_name="CEP", max_length=10, blank=True, default=""),
        ),
    ]

