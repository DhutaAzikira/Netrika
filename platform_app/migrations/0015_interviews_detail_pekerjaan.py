# Generated by Django 5.2.3 on 2025-06-24 17:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('platform_app', '0014_interviews_booking_code_interviews_jenis_wawancara_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='interviews',
            name='detail_pekerjaan',
            field=models.TextField(blank=True, null=True),
        ),
    ]
