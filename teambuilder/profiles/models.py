from django.db import models

from core.models import CustomUser, GENERATION_CHOICES, GERCHIKOV_CHOICES


class Role(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Название роли")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Роль"
        verbose_name_plural = "Роли"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Team(models.Model):
    manager = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="teams")
    name = models.CharField(max_length=150, verbose_name="Название команды")
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    employees = models.ManyToManyField("Employee", blank=True, related_name="teams")

    class Meta:
        verbose_name = "Команда"
        verbose_name_plural = "Команды"

    def __str__(self):
        return self.name


class Employee(models.Model):
    fio = models.CharField(max_length=255, verbose_name="ФИО")
    is_active_candidate = models.BooleanField(default=True, verbose_name="Активный кандидат")
    disc_scores = models.JSONField(null=True, blank=True, verbose_name="DISC баллы")
    gerchikov_type = models.CharField(
        max_length=50,
        choices=GERCHIKOV_CHOICES,
        verbose_name="Тип мотивации по Герчикову",
        blank=True,
    )
    age = models.PositiveIntegerField(verbose_name="Возраст")
    generation = models.CharField(max_length=10, choices=GENERATION_CHOICES, blank=True)
    role_in_team = models.CharField(max_length=100, blank=True, verbose_name="Роль в команде")
    salary_block = models.JSONField(null=True, blank=True, verbose_name="Блок зарплаты")
    motivation_expect = models.TextField(blank=True, verbose_name="Что хочет сотрудник")
    current_team = models.ForeignKey(
        "Team",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="current_members",
    )
    manager = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="employees",
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Сотрудник"
        verbose_name_plural = "Сотрудники"
        ordering = ["-created_at"]

    def __str__(self):
        return self.fio

    @staticmethod
    def calculate_generation_by_age(age):
        try:
            age = int(age)
        except (TypeError, ValueError):
            return ""

        if 13 <= age <= 28:
            return "Z"
        if 29 <= age <= 45:
            return "Y"
        if 46 <= age <= 61:
            return "X"
        if age >= 62:
            return "BB"
        return ""

    def save(self, *args, **kwargs):
        self.generation = self.calculate_generation_by_age(self.age)
        super().save(*args, **kwargs)

    @property
    def disc_primary(self):
        scores = self.disc_scores
        if not isinstance(scores, dict) or not scores:
            return "-"

        normalized_scores = {
            key: value
            for key, value in scores.items()
            if key in {"D", "I", "S", "C"} and isinstance(value, (int, float))
        }
        return max(normalized_scores, key=normalized_scores.get) if normalized_scores else "-"

    @property
    def salary_min(self):
        salary_block = self.salary_block if isinstance(self.salary_block, dict) else {}
        return salary_block.get("min", 0)

    def get_generation_display(self):
        generations = {
            "X": "Поколение X (1965–1980)",
            "BB": "Бэби-бумеры (1944–1964)",
            "Y": "Поколение Y / Миллениалы (1981–1996)",
            "Z": "Поколение Z (1997–2012)",
            "Alpha": "Поколение Alpha (2013+)",
        }
        return generations.get(self.generation, self.generation or "Не указано")
