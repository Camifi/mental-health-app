# Generated by Django 5.0.2 on 2024-02-22 22:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_message_professional'),
    ]

    operations = [
        migrations.AlterField(
            model_name='patient',
            name='therapist_gender_preference',
            field=models.CharField(blank=True, choices=[('M', 'Masculino'), ('F', 'Femenino')], max_length=1, verbose_name='Preferencia de Terapeuta'),
        ),
    ]