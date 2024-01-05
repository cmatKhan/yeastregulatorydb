# Generated by Django 4.2.8 on 2024-01-03 18:10

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("regulatory_data", "0005_alter_datasource_description"),
    ]

    operations = [
        migrations.AlterField(
            model_name="promoterset",
            name="notes",
            field=models.CharField(
                default="none", help_text="free entry text field, no more than 100 char long", max_length=500
            ),
        ),
    ]