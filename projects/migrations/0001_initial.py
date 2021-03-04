

import django.contrib.auth.models
from django.db import migrations, models
from django.contrib.postgres.fields import ArrayField


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Projects',
            fields=[
                ('id', models.AutoField(auto_created=True,
                                        primary_key=True, serialize=False, verbose_name='ID')),
                ('project_name', models.CharField(max_length=60)),
                ('project_owner', models.CharField(
                    default=django.contrib.auth.models.User, max_length=60)),
                ('project_created', models.DateTimeField(auto_now_add=True)),
                ('project_description', models.CharField(max_length=255)),
                ('project_allowed_viewers', models.CharField(max_length=6000)),
            ],
        ),
    ]
