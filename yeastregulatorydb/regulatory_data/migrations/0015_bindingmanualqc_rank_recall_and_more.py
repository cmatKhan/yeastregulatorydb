# Generated by Django 4.2.8 on 2024-01-19 20:34

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("regulatory_data", "0014_alter_expression_unique_together"),
    ]

    operations = [
        migrations.AddField(
            model_name="bindingmanualqc",
            name="rank_recall",
            field=models.CharField(
                choices=[("unreviewed", "unreviewed"), ("pass", "pass"), ("fail", "fail")],
                default="unreviewed",
                help_text="`pass` if at least 1 rank response bin in the first 100 genes ranked by pvalue is significant. Else `unreviewed` or `fail`",
            ),
        ),
        migrations.AlterField(
            model_name="bindingmanualqc",
            name="best_datatype",
            field=models.CharField(
                choices=[("unreviewed", "unreviewed"), ("pass", "pass"), ("fail", "fail")],
                default="unreviewed",
                help_text="`pass` if the only binding data that performs better is from the same binding source. Otherwise, `unreviewed` or `fail`",
            ),
        ),
        migrations.AlterField(
            model_name="bindingmanualqc",
            name="data_usable",
            field=models.CharField(
                choices=[("unreviewed", "unreviewed"), ("pass", "pass"), ("fail", "fail")],
                default="unreviewed",
                help_text="`pass` if there is no reason to believe the data has technical faults. Otherwise, `unreviewed` or `false`",
            ),
        ),
        migrations.AlterField(
            model_name="bindingmanualqc",
            name="passing_replicate",
            field=models.CharField(
                choices=[("unreviewed", "unreviewed"), ("pass", "pass"), ("fail", "fail")],
                default="unreviewed",
                help_text="Primarily, and probably only, relevant to Calling Cards data. `pass` if the replicate's hops should be counted towards the target hop count. `unreviewed` or `false` otherwise",
            ),
        ),
    ]