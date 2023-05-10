# Generated by Django 4.1.1 on 2023-05-09 00:59

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("sch", "0057_turnaround_date_alter_turnaround_unique_together"),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name="turnaround",
            unique_together=set(),
        ),
        migrations.AddField(
            model_name="turnaround",
            name="early_slot",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="early_turnarounds",
                to="sch.slot",
            ),
        ),
        migrations.AddField(
            model_name="turnaround",
            name="late_slot",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="late_turnarounds",
                to="sch.slot",
            ),
        ),
        migrations.AlterUniqueTogether(
            name="turnaround",
            unique_together={("employee", "early_slot", "late_slot")},
        ),
        migrations.RemoveField(
            model_name="turnaround",
            name="date",
        ),
        migrations.RemoveField(
            model_name="turnaround",
            name="slots",
        ),
    ]