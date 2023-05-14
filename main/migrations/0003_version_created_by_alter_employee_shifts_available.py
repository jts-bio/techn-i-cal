# Generated by Django 4.1.1 on 2023-05-01 00:21

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("main", "0002_profile"),
    ]

    operations = [
        migrations.AddField(
            model_name="version",
            name="created_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="versions_created",
                to="main.profile",
            ),
        ),
        migrations.AlterField(
            model_name="employee",
            name="shifts_available",
            field=models.ManyToManyField(
                blank=True,
                help_text="All shifts this employee is available to work and is in the active rotation for. \n                            Trained shifts not also marked as available will never be scheduled by the AI, \n                            but will allow for manual assignments.",
                related_name="employees_available",
                to="main.shift",
            ),
        ),
    ]
