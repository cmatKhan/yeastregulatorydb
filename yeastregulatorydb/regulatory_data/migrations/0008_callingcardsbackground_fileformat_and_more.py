# Generated by Django 4.2.8 on 2024-01-04 20:07

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("regulatory_data", "0007_alter_binding_file_alter_promotersetsig_promoter"),
    ]

    operations = [
        migrations.AddField(
            model_name="callingcardsbackground",
            name="fileformat",
            field=models.ForeignKey(
                default=1,
                help_text="The file format of the file",
                on_delete=django.db.models.deletion.CASCADE,
                to="regulatory_data.fileformat",
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="fileformat",
            name="fields",
            field=models.CharField(
                help_text='A JSON key:value set of columns and expected datatypes. Eg {"chr": "str","start": "int","end": "int","name": "str","score": "float","strand": ["+", "-", "*"]}. This gets checked for JSON validity at upload.',
                max_length=1000,
            ),
        ),
    ]
