from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [("encounters", "0003_priority_99")]

    operations = [
        migrations.RenameField(model_name="encounter", old_name="amount_cents", new_name="amount"),
    ]
