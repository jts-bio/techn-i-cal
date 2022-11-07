# Generated by Django 4.1.1 on 2022-10-13 11:36

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('sch', '0024_employee_employee_class'),
    ]

    operations = [
        migrations.CreateModel(
            name='TemplatedDayOff',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ppd_id', models.IntegerField()),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='sch.employee')),
            ],
        ),
    ]