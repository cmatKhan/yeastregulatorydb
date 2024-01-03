# Generated by Django 4.2.8 on 2024-01-02 16:21

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("regulatory_data", "0004_alter_datasource_citation"),
    ]

    operations = [
        migrations.AlterField(
            model_name="datasource",
            name="description",
            field=models.CharField(
                default="none",
                help_text="A description of the data. include a URL to github repo with scripts describing how the data was parsed",
                max_length=400,
            ),
        ),
    ]
