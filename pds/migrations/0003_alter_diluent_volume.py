# Generated by Django 4.1.1 on 2022-10-23 01:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pds', '0002_diluent_alter_drug_unit_size_compound'),
    ]

    operations = [
        migrations.AlterField(
            model_name='diluent',
            name='volume',
            field=models.FloatField(),
        ),
    ]