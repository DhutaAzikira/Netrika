# Generated by Django 5.2.3 on 2025-07-13 16:40

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('platform_app', '0019_remove_interviews_tier_interviews_package'),
    ]

    operations = [
        migrations.RenameField(
            model_name='userprofiles',
            old_name='sex',
            new_name='gender',
        ),
        migrations.RemoveField(
            model_name='userprofiles',
            name='email',
        ),
    ]
