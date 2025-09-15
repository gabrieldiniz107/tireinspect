from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ("service_orders", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="serviceorder",
            name="order_type",
            field=models.CharField(
                verbose_name="Tipo",
                max_length=10,
                choices=[("orcamento", "Orçamento"), ("servico", "Serviço")],
                default="servico",
            ),
        ),
        migrations.AddField(
            model_name="serviceorder",
            name="service_number",
            field=models.CharField(
                verbose_name="Número do serviço",
                max_length=30,
                default="",
            ),
        ),
        migrations.AddField(
            model_name="serviceorder",
            name="order_date",
            field=models.DateField(
                verbose_name="Data",
                default=django.utils.timezone.now,
            ),
        ),
    ]
