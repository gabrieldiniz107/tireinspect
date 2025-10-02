from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("service_orders", "0009_serviceordertruck_observation_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="serviceorder",
            name="is_draft",
            field=models.BooleanField(default=False),
        ),
    ]
