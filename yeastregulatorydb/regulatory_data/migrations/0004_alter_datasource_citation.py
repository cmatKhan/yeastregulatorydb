# Generated by Django 4.2.8 on 2024-01-02 16:05

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("regulatory_data", "0003_alter_datasource_description_alter_datasource_notes"),
    ]

    operations = [
        migrations.AlterField(
            model_name="datasource",
            name="citation",
            field=models.CharField(default="ask_admin", help_text="citation for the data", max_length=400),
        ),
    ]
