# Generated by Django 4.1.1 on 2023-05-09 00:47

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("sch", "0056_employee_initials_alter_employee_unique_together"),
    ]

    operations = [
        migrations.AddField(
            model_name="turnaround",
            name="date",
            field=models.DateField(null=True),
        ),
        migrations.AlterUniqueTogether(
            name="turnaround",
            unique_together={("employee", "date")},
        ),
    ]