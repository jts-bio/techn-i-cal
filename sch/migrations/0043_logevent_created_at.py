# Generated by Django 4.1.1 on 2023-03-02 09:09

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):
    dependencies = [
        ("sch", "0042_workday_pto_requests"),
    ]

    operations = [
        migrations.AddField(
            model_name="logevent",
            name="created_at",
            field=models.DateTimeField(
                auto_now_add=True, default=django.utils.timezone.now
            ),
            preserve_default=False,
        ),
    ]