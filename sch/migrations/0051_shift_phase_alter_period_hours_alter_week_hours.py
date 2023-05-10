# Generated by Django 4.1.1 on 2023-05-02 01:17

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("sch", "0050_alter_period_hours_alter_week_hours"),
    ]

    operations = [
        migrations.AddField(
            model_name="shift",
            name="phase",
            field=models.SmallIntegerField(
                choices=[(1, "AM"), (2, "MD"), (3, "PM"), (4, "EV"), (5, "XN")],
                default=-1,
            ),
        ),
        migrations.AlterField(
            model_name="period",
            name="hours",
            field=models.JSONField(blank=True, default=dict, null=True),
        ),
        migrations.AlterField(
            model_name="week",
            name="hours",
            field=models.JSONField(blank=True, default=dict, null=True),
        ),
    ]