# Generated by Django 4.1.1 on 2023-04-21 03:29

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("sch", "0049_alter_period_hours_alter_shift_occur_days_turnaround"),
    ]

    operations = [
        migrations.AlterField(
            model_name="period",
            name="hours",
            field=models.JSONField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="week",
            name="hours",
            field=models.JSONField(blank=True, null=True),
        ),
    ]