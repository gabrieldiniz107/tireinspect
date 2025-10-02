from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0009_remove_tire_groove_4_alter_tire_groove_1_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="truck",
            name="fleet",
            field=models.CharField(verbose_name="Frota", max_length=50, blank=True, default=""),
        ),
    ]
