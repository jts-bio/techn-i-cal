# Generated by Django 4.1.1 on 2023-01-13 15:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sch', '0021_slot_fills_with'),
    ]

    operations = [
        migrations.AddField(
            model_name='employee',
            name='image_url',
            field=models.CharField(default='/static/img/CuteRobot-01.png', max_length=300),
        ),
    ]