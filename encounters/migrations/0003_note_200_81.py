from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("encounters", "0002_region_99")]

    operations = [
        migrations.AlterField(model_name="encounter", name="note", field=models.CharField(blank=True, default="", max_length=200)),
    ]
