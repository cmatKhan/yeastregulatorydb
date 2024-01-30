# Generated by Django 4.2.8 on 2024-01-19 01:04

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("regulatory_data", "0012_expression_strain_alter_expression_batch_and_more"),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name="expression",
            unique_together={
                ("regulator", "batch", "replicate", "control", "mechanism", "restriction", "time", "source")
            },
        ),
    ]