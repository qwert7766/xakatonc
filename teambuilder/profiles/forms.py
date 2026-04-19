from django import forms

from .disc_data import DISC_QUESTIONS
from .models import Employee, Role, Team


class EmployeeRegistrationForm(forms.ModelForm):
    fio = forms.CharField(max_length=255, label="ФИО")
    age = forms.IntegerField(min_value=14, label="Возраст")
    generation_display = forms.CharField(
        required=False,
        label="Поколение",
        widget=forms.TextInput(attrs={"class": "form-control", "readonly": "readonly"}),
    )
    role = forms.ModelChoiceField(
        queryset=Role.objects.none(),
        label="Роль в команде",
        empty_label="Выберите роль",
    )
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
        fields = (
            "fio",
            "age",
            "generation_display",
            "gerchikov_type",
            "motivation_expect",
            "notes",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["role"].queryset = Role.objects.order_by("name")
        age_value = self.data.get("age") or self.initial.get("age")
        self.fields["generation_display"].initial = self.get_generation_label(age_value)

    @staticmethod
    def get_generation_code(age):
        try:
            age = int(age)
        except (TypeError, ValueError):
            return ""

        if age >= 13 and age <= 28:
            return "Z"
        if age >= 29 and age <= 45:
            return "Y"
        if age >= 46 and age <= 61:
            return "X"
        if age >= 62:
            return "BB"
        return ""

    @classmethod
    def get_generation_label(cls, age):
        generation_code = cls.get_generation_code(age)
        choices = dict(Employee._meta.get_field("generation").choices)
        return choices.get(generation_code, "")

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.is_active_candidate = True
        instance.disc_scores = {"D": 0, "I": 0, "S": 0, "C": 0}
        instance.generation = self.get_generation_code(self.cleaned_data.get("age"))
        selected_role = self.cleaned_data.get("role")
        instance.role_in_team = selected_role.name if selected_role else ""
        instance.salary_block = {
            "min": self.cleaned_data["salary_min"],
            "motivation": self.cleaned_data["salary_motivation"],
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
        fields = ["name", "description"]
        widgets = {
            "name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Название команды"}
            ),
            "description": forms.Textarea(
                attrs={"class": "form-control", "rows": 3, "placeholder": "Описание команды"}
            ),
        }
        labels = {
            "name": "Название команды",
            "description": "Описание",
        }
