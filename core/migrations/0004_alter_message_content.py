# Generated by Django 5.0.2 on 2024-02-23 00:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_alter_patient_therapist_gender_preference'),
    ]

    operations = [
        migrations.AlterField(
            model_name='message',
            name='content',
            field=models.TextField(max_length=256),
        ),
    ]
