# Generated by Django 4.1.1 on 2023-04-10 10:46

import datetime
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("sch", "0047_employee_std_wk_max_schedule_prn_maxes_and_more"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="schedule",
            name="prn_maxes",
        ),
        migrations.AlterField(
            model_name="scheduleemusr",
            name="schedule",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="emusr",
                to="sch.schedule",
            ),
        ),
        migrations.AlterField(
            model_name="shift",
            name="duration",
            field=models.DurationField(default=datetime.timedelta(seconds=37800)),
        ),
        migrations.AlterField(
            model_name="shift",
            name="hours",
            field=models.FloatField(default=10),
        ),
        migrations.AlterField(
            model_name="shift",
            name="start",
            field=models.TimeField(default=datetime.time(7, 0)),
        ),
        migrations.DeleteModel(
            name="SchedulingMax",
        ),
    ]
