# Generated by Django 4.1.1 on 2022-10-27 12:49

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('sch', '0040_remove_week_workdays_workday_week'),
    ]

    operations = [
        migrations.AlterField(
            model_name='workday',
            name='week',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='sch.week'),
        ),
    ]