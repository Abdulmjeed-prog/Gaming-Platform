from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('notifications', '0003_alter_notification_id'),
        ('accounts', '0005_remove_profile_role'),
    ]

    operations = [
        migrations.CreateModel(
            name='DeveloperAnnouncement',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('content', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('developer', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='announcements',
                    to='accounts.developerprofile'
                )),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
    ]
