from django import forms
from .disc_data import DISC_QUESTIONS
from .models import Employee, Team
 
 
class EmployeeRegistrationForm(forms.ModelForm):
    fio = forms.CharField(max_length=255, label="ФИО")
    age = forms.IntegerField(min_value=14, label="Возраст")
    generation = forms.ChoiceField(
        choices=Employee._meta.get_field("generation").choices,
        label="Поколение",
    )
    role_in_team = forms.CharField(max_length=100, label="Роль в команде")
    gerchikov_type = forms.ChoiceField(
        choices=Employee._meta.get_field("gerchikov_type").choices,
        label="Тип мотивации",
    )
    motivation_expect = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 3}),
        label="Что для вас важно в работе",
    )
    salary_min = forms.IntegerField(min_value=0, label="Желаемая зарплата от")
    salary_motivation = forms.CharField(
        max_length=255,
        label="Что мотивирует",
        help_text="Например: бонусы, стабильность, рост",
    )
    salary_development = forms.CharField(
        max_length=255,
        label="Какое развитие важно",
        help_text="Например: обучение, карьерный рост, новые задачи",
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"rows": 2}),
        label="Комментарий",
    )
 
    class Meta:
        model = Employee
        fields = ('fio', 'age', 'generation', 'role_in_team', 'gerchikov_type', 'motivation_expect', 'notes')
 
    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.is_active_candidate = True
        instance.disc_scores = {"D": 0, "I": 0, "S": 0, "C": 0}
        instance.salary_block = {
            "min":         self.cleaned_data["salary_min"],
            "motivation":  self.cleaned_data["salary_motivation"],
            "development": self.cleaned_data["salary_development"],
        }
        if commit:
            instance.save()
            self.created_employee = instance
        else:
            self.created_employee = None
        return instance
 
 
class DiscTestForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for question in DISC_QUESTIONS:
            self.fields[question["id"]] = forms.ChoiceField(
                label=question["text"],
                choices=question["choices"],
                widget=forms.RadioSelect,
                required=True,
            )
 
    def calculate_scores(self):
        scores = {"D": 0, "I": 0, "S": 0, "C": 0}
        for answer in self.cleaned_data.values():
            if answer in scores:
                scores[answer] += 1
        total = sum(scores.values()) or 1
        return {k: round(v * 100 / total) for k, v in scores.items()}
 

class TeamForm(forms.ModelForm):
    class Meta:
        model = Team
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Название команды'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Описание команды'}),
        }
        labels = {
            'name': 'Название команды',
            'description': 'Описание',
        }