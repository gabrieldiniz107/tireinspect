from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ("service_orders", "0010_add_is_draft_to_serviceorder"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="serviceordertruck",
            name="created_by",
            field=models.ForeignKey(blank=True, null=True, on_delete=models.deletion.PROTECT, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name="serviceordertruck",
            name="truck_number",
            field=models.PositiveIntegerField(blank=True, null=True, db_index=True),
        ),
        migrations.AddConstraint(
            model_name="serviceordertruck",
            constraint=models.UniqueConstraint(fields=("created_by", "truck_number"), name="uniq_truck_number_per_user"),
        ),
    ]

