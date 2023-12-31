# Generated by Django 4.2.8 on 2024-01-04 23:55

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("regulatory_data", "0008_callingcardsbackground_fileformat_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="fileformat",
            name="fields",
            field=models.JSONField(
                help_text='A JSON key:value set of columns and expected datatypes. Eg {"chr": "str","start": "int","end": "int","name": "str","score": "float","strand": ["+", "-", "*"]}'
            ),
        ),
    ]
