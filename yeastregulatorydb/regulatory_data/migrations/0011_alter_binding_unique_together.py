# Generated by Django 4.2.8 on 2024-01-08 20:22

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("regulatory_data", "0010_binding_condition"),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name="binding",
            unique_together={("regulator", "batch", "condition", "replicate", "source")},
        ),
    ]
