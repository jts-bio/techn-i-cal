# Generated by Django 4.1.1 on 2022-09-14 22:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("sch", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="workday",
            name="ppd_id",
            field=models.IntegerField(default=17, editable=False),
            preserve_default=False,
        ),
    ]