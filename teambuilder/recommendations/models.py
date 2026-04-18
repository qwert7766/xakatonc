# recommendations/models.py
from django.db import models
from core.models import CustomUser, GERCHIKOV_CHOICES, GENERATION_CHOICES
 
 
ROLE_FUNCTION_CHOICES = [
    ('sells',      'Продаёт / привлекает клиентов'),
    ('analyzes',   'Анализирует данные / строит отчёты'),
    ('supports',   'Поддерживает клиентов / решает проблемы'),
    ('leads',      'Руководит людьми / принимает решения'),
    ('creates',    'Создаёт продукт / пишет код'),
    ('processes',  'Обрабатывает документы / выполняет регламенты'),
    ('recruits',   'Нанимает / работает с людьми'),
    ('negotiates', 'Ведёт переговоры / работает с партнёрами'),
]
 
LEADERSHIP_STYLE_CHOICES = [
    ('authoritarian', 'Авторитарный — чёткие задачи, контроль'),
    ('democratic',    'Демократический — обсуждение, команда'),
    ('coaching',      'Коучинг — развитие, поддержка'),
    ('delegating',    'Делегирующий — автономия, результат'),
]
 
 
class IdealProfile(models.Model):
    manager = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='ideal_profiles'
    )
 
    target_role = models.CharField(
        max_length=200,
        verbose_name="Название роли / позиции"
    )
 
    role_functions = models.JSONField(
        default=list,
        verbose_name="Функции роли",
        help_text="['sells', 'negotiates'] — что реально делает человек"
    )
 
    disc_preferred = models.JSONField(
        verbose_name="Желаемый DISC профиль",
        help_text='{"D": 70, "I": 80, "S": 40, "C": 30}'
    )
 
    preferred_personality_types = models.JSONField(
        default=list,
        verbose_name="Предпочитаемые типы личности",
        help_text='["S", "C"]'
    )
 
    gerchikov_preferred = models.CharField(
        max_length=50,
        choices=GERCHIKOV_CHOICES,
        null=True,
        blank=True,
        verbose_name="Предпочитаемый тип мотивации по Герчикову"
    )
 
    age_min = models.PositiveIntegerField(default=20, verbose_name="Возраст от")
    age_max = models.PositiveIntegerField(default=50, verbose_name="Возраст до")
 
    generation_preferred = models.CharField(
        max_length=10,
        choices=GENERATION_CHOICES,
        null=True,
        blank=True,
        verbose_name="Предпочитаемое поколение"
    )
 
    leadership_style = models.CharField(
        max_length=50,
        choices=LEADERSHIP_STYLE_CHOICES,
        default='democratic',
        verbose_name="Ваш стиль управления"
    )
 
    motivation_style = models.TextField(
        blank=True,
        verbose_name="Как планируете мотивировать сотрудника?"
    )
 
    team_compatibility_note = models.TextField(
        blank=True,
        verbose_name="Дополнительные пожелания"
    )
 
    is_for_existing_team = models.BooleanField(
        default=False,
        verbose_name="Подбор в существующую команду?"
    )
 
    team = models.ForeignKey(
        'profiles.Team',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Команда (если подбор в существующую)"
    )
 
    created_at = models.DateTimeField(auto_now_add=True)
 
    class Meta:
        verbose_name = "Идеальный профиль"
        verbose_name_plural = "Идеальные профили"
        ordering = ['-created_at']
 
    def __str__(self):
        return f"{self.target_role} — {self.manager.get_full_name() or self.manager.username}"
 
 
class RecommendationLog(models.Model):
    manager = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        verbose_name="Руководитель"
    )
    ideal_profile = models.ForeignKey(
        IdealProfile,
        on_delete=models.CASCADE,
        verbose_name="Идеальный профиль"
    )
    employee = models.ForeignKey(
        'profiles.Employee',
        on_delete=models.CASCADE,
        verbose_name="Рекомендованный сотрудник"
    )
 
    match_score = models.FloatField(
        null=True,
        blank=True,
        verbose_name="Итоговый балл (0-100)"
    )
 
    score_breakdown = models.JSONField(
        default=dict,
        verbose_name="Детализация по осям"
    )
 
    status = models.CharField(
        max_length=20,
        choices=[
            ('taken',    'Взят в команду'),
            ('good',     'Хороший кандидат'),
            ('average',  'Средний кандидат'),
            ('rejected', 'Отклонён'),
            ('none',     'Без оценки'),
        ],
        default='none',
        verbose_name="Статус"
    )
 
    works_well_in_team  = models.BooleanField(default=False, verbose_name="Хорошо работает в команде")
    productive          = models.BooleanField(default=False, verbose_name="Продуктивный")
    fits_manager_style  = models.BooleanField(default=False, verbose_name="Подходит под стиль управления")
    motivation_match    = models.BooleanField(default=False, verbose_name="Мотивация совпадает")
 
    potential_issues = models.TextField(blank=True, verbose_name="Риски / минусы")
    comment          = models.TextField(blank=True, verbose_name="Комментарий руководителя")
 
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
 
    class Meta:
        ordering = ['-match_score', '-created_at']
        verbose_name = "Лог рекомендации"
        verbose_name_plural = "Логи рекомендаций"
 
    def __str__(self):
        return f"{self.employee.fio} — {self.match_score:.1f}% — {self.get_status_display()}" if self.match_score else f"{self.employee.fio} — {self.get_status_display()}"