# Generated by Django 4.1.1 on 2022-09-29 15:12

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("sch", "0016_delete_photo_alter_slot_unique_together_and_more"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="workday",
            name="shifts",
        ),
    ]