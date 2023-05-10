# Generated by Django 4.1.1 on 2023-05-06 14:19

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("sch", "0054_schedule_department"),
    ]

    operations = [
        migrations.AlterField(
            model_name="department",
            name="org",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="departments",
                to="sch.organization",
            ),
        ),
        migrations.AlterField(
            model_name="period",
            name="hours",
            field=models.JSONField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="schedule",
            name="data",
            field=models.JSONField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="schedule",
            name="weekly_hours",
            field=models.JSONField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="week",
            name="hours",
            field=models.JSONField(blank=True, null=True),
        ),
    ]