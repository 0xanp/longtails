# Generated by Django 4.0.6 on 2022-07-20 18:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('freemasons', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='freemasonproject',
            name='last_sync_at',
            field=models.DateTimeField(),
        ),
    ]