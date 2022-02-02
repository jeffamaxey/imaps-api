# Generated by Django 3.2 on 2022-02-02 01:06

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('analysis', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Species',
            fields=[
                ('id', models.CharField(max_length=2, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=50)),
                ('latin_name', models.CharField(max_length=50)),
                ('ensembl_id', models.CharField(max_length=50)),
                ('official_version', models.OneToOneField(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='species_official', to='analysis.job')),
            ],
            options={
                'db_table': 'species',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='Gene',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=20)),
                ('species', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='genes', to='genomes.species')),
            ],
            options={
                'db_table': 'genes',
                'ordering': ['name'],
            },
        ),
    ]
