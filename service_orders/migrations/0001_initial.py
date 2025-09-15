from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ServiceOrder',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False, auto_created=True, verbose_name='ID')),
                ('client', models.CharField(max_length=120, verbose_name='Cliente')),
                ('cnpj_cpf', models.CharField(max_length=20, verbose_name='CNPJ/CPF')),
                ('vehicle_plate', models.CharField(max_length=10, verbose_name='Placa do veículo')),
                ('city', models.CharField(max_length=80, verbose_name='Cidade')),
                ('manufacturer', models.CharField(max_length=80, verbose_name='Fabricante')),
                ('cep', models.CharField(max_length=10, verbose_name='CEP')),
                ('fleet', models.CharField(blank=True, max_length=50, verbose_name='Frota')),
                ('model', models.CharField(blank=True, max_length=80, verbose_name='Modelo')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(on_delete=models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at', '-id'],
            },
        ),
    ]

