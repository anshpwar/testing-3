from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("encounters", "0001_initial")]

    operations = [
        migrations.AddField(model_name="encounter", name="region", field=models.CharField(blank=True, default="", max_length=8)),
    ]
