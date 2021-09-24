# Generated by Django 3.2 on 2021-09-24 14:03

import core.models
from django.db import migrations, models
import django.db.models.deletion
import time


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Group',
            fields=[
                ('id', models.BigIntegerField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=50)),
                ('slug', models.SlugField(unique=True, validators=[core.models.slug_validator])),
                ('description', models.CharField(max_length=200)),
            ],
            options={
                'db_table': 'groups',
            },
        ),
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.BigIntegerField(primary_key=True, serialize=False)),
                ('username', models.SlugField(max_length=30, unique=True, validators=[core.models.slug_validator])),
                ('email', models.EmailField(max_length=200, unique=True)),
                ('password', models.CharField(max_length=128)),
                ('last_login', models.IntegerField(default=None, null=True)),
                ('created', models.IntegerField(default=time.time)),
                ('name', models.CharField(max_length=50)),
                ('image', models.ImageField(default='', upload_to=core.models.create_filename)),
                ('password_reset_token', models.CharField(default='', max_length=128)),
                ('password_reset_token_expiry', models.IntegerField(default=0)),
            ],
            options={
                'db_table': 'users',
                'ordering': ['created'],
            },
        ),
        migrations.CreateModel(
            name='UserGroupLink',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('permission', models.IntegerField(choices=[[1, 'invited'], [2, 'member'], [3, 'admin']], default=1)),
                ('group', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.group')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.user')),
            ],
            options={
                'db_table': 'user_group_links',
            },
        ),
        migrations.AddField(
            model_name='group',
            name='users',
            field=models.ManyToManyField(related_name='groups', through='core.UserGroupLink', to='core.User'),
        ),
    ]
