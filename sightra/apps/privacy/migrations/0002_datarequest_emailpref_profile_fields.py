from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("privacy", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="privacyprofile",
            name="optional_cookies",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="privacyprofile",
            name="marketing_emails_opt_in",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="privacyprofile",
            name="age_confirmed_adult",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="privacyprofile",
            name="parental_consent_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="privacyprofile",
            name="guardian_email",
            field=models.EmailField(blank=True, max_length=254),
        ),
        migrations.CreateModel(
            name="DataRequest",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("kind", models.CharField(db_index=True, max_length=32)),
                ("email", models.EmailField(max_length=254)),
                ("guardian_email", models.EmailField(blank=True, max_length=254)),
                ("details", models.TextField(blank=True)),
                ("status", models.CharField(db_index=True, default="open", max_length=16)),
                ("supabase_user_id", models.CharField(blank=True, max_length=64)),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("processed_at", models.DateTimeField(blank=True, null=True)),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="EmailPreference",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("email", models.EmailField(max_length=254, unique=True)),
                ("marketing_opt_in", models.BooleanField(default=False)),
                ("unsubscribed_at", models.DateTimeField(blank=True, null=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
        ),
    ]
