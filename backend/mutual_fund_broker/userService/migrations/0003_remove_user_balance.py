# Generated by Django 4.2.18 on 2025-01-18 06:03

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("userService", "0002_user_balance"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="user",
            name="balance",
        ),
    ]
