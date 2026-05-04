"""Auto-generated migration to add processed_file to VideoSource."""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("cameras", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="videosource",
            name="processed_file",
            field=models.FileField(upload_to="annotated/", blank=True, null=True, help_text="Processed / annotated video file"),
        ),
    ]
