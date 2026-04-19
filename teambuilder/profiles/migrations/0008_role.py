from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("profiles", "0007_alter_employee_generation"),
    ]

    operations = [
        migrations.CreateModel(
            name="Role",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=100, unique=True, verbose_name="Название роли")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "verbose_name": "Роль",
                "verbose_name_plural": "Роли",
                "ordering": ["name"],
            },
        ),
    ]
