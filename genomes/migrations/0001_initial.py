# Generated by Django 3.2 on 2022-01-17 08:04

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Gene',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=20)),
                ('species', models.CharField(max_length=2)),
            ],
            options={
                'db_table': 'genes',
                'ordering': ['name'],
            },
        ),
    ]
