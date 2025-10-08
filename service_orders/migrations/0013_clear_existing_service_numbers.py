from django.db import migrations


def clear_service_numbers(apps, schema_editor):
    Order = apps.get_model("service_orders", "ServiceOrder")
    Order.objects.exclude(service_number="").update(service_number="")


class Migration(migrations.Migration):

    dependencies = [
        ("service_orders", "0012_backfill_truck_created_by"),
    ]

    operations = [
        migrations.RunPython(clear_service_numbers, migrations.RunPython.noop),
    ]

