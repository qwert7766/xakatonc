from django.db import models
from core.models import CustomUser, GERCHIKOV_CHOICES, GENERATION_CHOICES
 
 
class Team(models.Model):
    manager     = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='teams')
    name        = models.CharField(max_length=150, verbose_name="Название команды")
    description = models.TextField(blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)
    employees   = models.ManyToManyField('Employee', blank=True, related_name='teams')
    
    class Meta:
        verbose_name = "Команда"
        verbose_name_plural = "Команды"
 
    def __str__(self):
        return self.name
 
 
class Employee(models.Model):
    fio                 = models.CharField(max_length=255, verbose_name="ФИО")
    is_active_candidate = models.BooleanField(default=True, verbose_name="Активный кандидат")
 
    disc_scores = models.JSONField(null=True, blank=True, verbose_name="DISC баллы")
 
    gerchikov_type = models.CharField(
        max_length=50, choices=GERCHIKOV_CHOICES,
        verbose_name="Тип мотивации по Герчикову", blank=True,
    )
 
    age          = models.PositiveIntegerField(verbose_name="Возраст")
    generation   = models.CharField(max_length=10, choices=GENERATION_CHOICES, blank=True)
    role_in_team = models.CharField(max_length=100, blank=True, verbose_name="Роль в команде")
 
    salary_block      = models.JSONField(null=True, blank=True, verbose_name="Блок зарплаты")
    motivation_expect = models.TextField(blank=True, verbose_name="Что хочет сотрудник")
 
    current_team = models.ForeignKey(
        'Team', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='current_members'  # ← ДОБАВЬТЕ ЭТО
    )
    # Руководитель назначается вручную в админке после регистрации
    manager = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='employees',
    )
 
    notes      = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
 
    class Meta:
        verbose_name = "Сотрудник"
        verbose_name_plural = "Сотрудники"
        ordering = ['-created_at']
 
    def __str__(self):
        return self.fio
 
    @property
    def disc_primary(self):
        s = self.disc_scores or {}
        return max(s, key=s.get) if s else '—'
 
    @property
    def salary_min(self):
        return (self.salary_block or {}).get('min', 0)