# Generated by Django 2.2.16 on 2020-12-05 09:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='group',
            name='name',
            field=models.SlugField(unique=True),
        ),
    ]