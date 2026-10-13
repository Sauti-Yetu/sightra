from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="UserPreference",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("supabase_user_id", models.CharField(max_length=64, unique=True)),
                ("email", models.EmailField(blank=True, max_length=254)),
                ("theme", models.CharField(default="light", max_length=16)),
                ("accessibility_json", models.JSONField(blank=True, default=dict)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
        ),
    ]
