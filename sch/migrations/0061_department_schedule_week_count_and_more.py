# Generated by Django 4.1.1 on 2023-05-12 06:02

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("sch", "0060_alter_employee_user"),
    ]

    operations = [
        migrations.AddField(
            model_name="department",
            name="schedule_week_count",
            field=models.IntegerField(default=6),
        ),
        migrations.AlterField(
            model_name="employee",
            name="department",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="employees",
                to="sch.department",
            ),
        ),
    ]