# Generated by Django 4.1.1 on 2022-11-28 05:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sch', '0063_schedule_slug'),
    ]

    operations = [
        migrations.AlterField(
            model_name='schedule',
            name='slug',
            field=models.CharField(default='', max_length=20),
        ),
    ]
