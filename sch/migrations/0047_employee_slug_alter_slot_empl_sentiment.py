# Generated by Django 4.1.1 on 2022-11-21 09:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sch', '0046_slot_empl_sentiment'),
    ]

    operations = [
        migrations.AddField(
            model_name='employee',
            name='slug',
            field=models.SlugField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='slot',
            name='empl_sentiment',
            field=models.SmallIntegerField(),
        ),
    ]
