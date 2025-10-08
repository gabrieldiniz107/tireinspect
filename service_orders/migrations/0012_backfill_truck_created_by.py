from django.db import migrations


def copy_created_by_from_order(apps, schema_editor):
    Truck = apps.get_model("service_orders", "ServiceOrderTruck")
    for t in Truck.objects.filter(created_by__isnull=True).select_related("order"):
        if getattr(t, "order", None) and getattr(t.order, "created_by_id", None):
            t.created_by_id = t.order.created_by_id
            t.save(update_fields=["created_by"])


class Migration(migrations.Migration):

    dependencies = [
        ("service_orders", "0011_serviceordertruck_truck_number_created_by"),
    ]

    operations = [
        migrations.RunPython(copy_created_by_from_order, migrations.RunPython.noop),
    ]

