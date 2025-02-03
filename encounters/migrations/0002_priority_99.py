from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("encounters", "0001_initial")]

    operations = [
        migrations.AddField(model_name="encounter", name="priority", field=models.IntegerField(default=0)),
    ]
