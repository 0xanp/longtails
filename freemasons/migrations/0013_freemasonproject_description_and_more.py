# Generated by Django 4.0.6 on 2022-07-22 18:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('freemasons', '0012_freemasonproject_last_summarized_at'),
    ]

    operations = [
        migrations.AddField(
            model_name='freemasonproject',
            name='description',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='freemasonproject',
            name='discord',
            field=models.CharField(blank=True, max_length=256, null=True),
        ),
        migrations.AddField(
            model_name='freemasonproject',
            name='name',
            field=models.CharField(blank=True, max_length=256, null=True),
        ),
        migrations.AddField(
            model_name='freemasonproject',
            name='opensea',
            field=models.CharField(blank=True, max_length=256, null=True),
        ),
        migrations.AddField(
            model_name='freemasonproject',
            name='twitter',
            field=models.CharField(blank=True, max_length=256, null=True),
        ),
    ]
