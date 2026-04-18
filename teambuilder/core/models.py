from django.contrib.auth.models import AbstractUser
from django.db import models
 
GERCHIKOV_CHOICES = [
    ('instrumental',   'Инструментальный (деньги / результат)'),
    ('professional',   'Профессиональный (рост / мастерство)'),
    ('patriotic',      'Патриотический (причастность / команда)'),
    ('administrative', 'Административный (статус / стабильность)'),
    ('master',         'Хозяйский (автономия / ответственность)'),
    ('mixed',          'Смешанный'),
]
 
GENERATION_CHOICES = [
    ('X',     'Поколение X (1965–1980)'),
    ('Y',     'Поколение Y / Миллениалы (1981–1996)'),
    ('Z',     'Поколение Z (1997–2012)'),
    ('Alpha', 'Поколение Alpha (2013+)'),
]
 
 
class CustomUser(AbstractUser):
    is_manager  = models.BooleanField(default=True,  verbose_name="Руководитель")
    is_employee = models.BooleanField(default=False, verbose_name="Сотрудник")
 
    # DISC профиль руководителя
    # Заполняется после прохождения DISC-теста
    disc_profile = models.JSONField(
        null=True,
        blank=True,
        verbose_name="DISC профиль руководителя",
        help_text='{"D": 80, "I": 40, "S": 30, "C": 60}'
    )
 
    gerchikov_type = models.CharField(
        max_length=50,
        choices=GERCHIKOV_CHOICES,
        null=True,
        blank=True,
        verbose_name="Тип мотивации по Герчикову"
    )
 
    age        = models.PositiveIntegerField(null=True, blank=True, verbose_name="Возраст")
    generation = models.CharField(
        max_length=10,
        choices=GENERATION_CHOICES,
        null=True,
        blank=True,
        verbose_name="Поколение"
    )
 
    # Стиль управления — используется в scorer для расчёта поколения
    leadership_style = models.CharField(
        max_length=50,
        choices=[
            ('authoritarian', 'Авторитарный'),
            ('democratic',    'Демократический'),
            ('coaching',      'Коучинг'),
            ('delegating',    'Делегирующий'),
        ],
        null=True,
        blank=True,
        verbose_name="Стиль управления"
    )
 
    role_style = models.TextField(blank=True, verbose_name="Описание стиля управления")
 
    class Meta:
        verbose_name        = "Пользователь"
        verbose_name_plural = "Пользователи"
 
    def __str__(self):
        return self.get_full_name() or self.username
 
    @property
    def disc_primary(self) -> str:
        profile = self.disc_profile or {}
        if not profile:
            return '—'
        return max(profile, key=profile.get)