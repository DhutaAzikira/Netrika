# Generated by Django 5.2.3 on 2025-07-14 07:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('platform_app', '0020_rename_sex_userprofiles_gender_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userprofiles',
            name='profile_picture',
            field=models.TextField(blank=True, help_text='URL to the profile picture', null=True),
        ),
    ]
