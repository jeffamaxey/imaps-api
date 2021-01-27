# Generated by Django 2.2.16 on 2021-01-27 01:20

from django.db import migrations, models
import django.db.models.deletion
import time


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0009_auto_20210114_1422'),
    ]

    operations = [
        migrations.CreateModel(
            name='Sample',
            fields=[
                ('id', models.BigIntegerField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=50)),
                ('creation_time', models.IntegerField(default=time.time)),
                ('last_modified', models.IntegerField(default=time.time)),
                ('description', models.TextField(blank=True, default='')),
                ('source', models.CharField(max_length=100)),
                ('organism', models.CharField(max_length=100)),
                ('qc_pass', models.NullBooleanField()),
                ('qc_message', models.CharField(max_length=100)),
                ('pi_name', models.CharField(max_length=100)),
                ('annotator_name', models.CharField(max_length=100)),
                ('collection', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='samples', to='core.Collection')),
            ],
            options={
                'db_table': 'samples',
                'ordering': ['-creation_time'],
            },
        ),
    ]
