# Generated by Django 4.1.1 on 2023-01-23 17:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sch', '0028_employee_active_schedule_employees'),
    ]

    operations = [
        migrations.AlterField(
            model_name='schedule',
            name='employees',
            field=models.ManyToManyField(related_name='schedules', to='sch.employee'),
        ),
    ]
