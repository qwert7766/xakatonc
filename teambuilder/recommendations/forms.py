from django import forms

from core.models import GERCHIKOV_CHOICES
from profiles.models import Role

from .models import IdealProfile, LEADERSHIP_STYLE_CHOICES, ROLE_FUNCTION_CHOICES


class IdealProfileForm(forms.ModelForm):
    leadership_style_display = forms.CharField(
        required=False,
        label="Ваш стиль управления",
        help_text="Подставляется автоматически из профиля текущего аккаунта",
        widget=forms.TextInput(attrs={"class": "form-control", "readonly": "readonly"}),
    )

    target_role = forms.ChoiceField(
        label="Роль / позиция",
        choices=[("", "— выберите роль —")],
        widget=forms.Select(attrs={"class": "form-select"}),
        required=True,
    )

    role_functions = forms.MultipleChoiceField(
        choices=ROLE_FUNCTION_CHOICES,
        widget=forms.CheckboxSelectMultiple(attrs={"class": "form-check-input"}),
        required=True,
        label="Что будет делать этот человек?",
        help_text="Выбери всё подходящее — на основе этого подберём мотивационный профиль",
    )

    disc_d = forms.IntegerField(
        min_value=0,
        max_value=100,
        initial=50,
        label="D — Доминантность",
        help_text="Решительность, напористость, готовность брать ответственность",
        widget=forms.NumberInput(attrs={"type": "range", "class": "form-range"}),
    )
    disc_i = forms.IntegerField(
        min_value=0,
        max_value=100,
        initial=50,
        label="I — Влиятельность",
        help_text="Общительность, умение убеждать, работа с людьми",
        widget=forms.NumberInput(attrs={"type": "range", "class": "form-range"}),
    )
    disc_s = forms.IntegerField(
        min_value=0,
        max_value=100,
        initial=50,
        label="S — Стабильность",
        help_text="Надёжность, спокойствие, исполнительность",
        widget=forms.NumberInput(attrs={"type": "range", "class": "form-range"}),
    )
    disc_c = forms.IntegerField(
        min_value=0,
        max_value=100,
        initial=50,
        label="C — Аналитичность",
        help_text="Точность, системность, внимание к деталям",
        widget=forms.NumberInput(attrs={"type": "range", "class": "form-range"}),
    )

    gerchikov_preferred = forms.ChoiceField(
        choices=[("", "— не важно —")] + list(GERCHIKOV_CHOICES),
        required=False,
        label="Предпочитаемый тип мотивации",
        help_text="По методологии Герчикова — что движет этим человеком?",
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    age_min = forms.IntegerField(
        min_value=18,
        max_value=70,
        initial=25,
        label="Возраст от",
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )
    age_max = forms.IntegerField(
        min_value=18,
        max_value=70,
        initial=45,
        label="до",
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )

    motivation_style = forms.CharField(
        required=False,
        label="Как планируете мотивировать сотрудника?",
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 2,
                "placeholder": "Например: премии за результат, карьерный рост, интересные задачи",
            }
        ),
    )

    is_for_existing_team = forms.BooleanField(
        required=False,
        label="Подбор в уже существующую команду?",
    )

    class Meta:
        model = IdealProfile
        fields = [
            "target_role",
            "role_functions",
            "gerchikov_preferred",
            "leadership_style_display",
            "motivation_style",
            "is_for_existing_team",
            "team",
        ]

    def __init__(self, *args, manager=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.manager = manager

        roles = list(Role.objects.values_list("name", flat=True).order_by("name"))
        if roles:
            role_choices = [("", "— выберите роль —")] + [(role, role) for role in roles]
        else:
            role_choices = [("", "— сначала добавьте роли в админке —")]
        self.fields["target_role"].choices = role_choices

        if manager:
            self.fields["team"].queryset = manager.teams.all()
            self.fields["team"].required = False
            self.fields["team"].label = "Выбери команду"
            self.fields["team"].widget.attrs["class"] = "form-select"
            leadership_value = manager.leadership_style or "democratic"
        elif self.instance and self.instance.pk:
            leadership_value = self.instance.leadership_style or "democratic"
        else:
            leadership_value = "democratic"

        leadership_label_map = dict(LEADERSHIP_STYLE_CHOICES)
        self.fields["leadership_style_display"].initial = leadership_label_map.get(
            leadership_value,
            leadership_value,
        )

        if self.instance and self.instance.pk and self.instance.disc_preferred:
            disc_profile = self.instance.disc_preferred
            self.initial.update(
                {
                    "disc_d": disc_profile.get("D", 50),
                    "disc_i": disc_profile.get("I", 50),
                    "disc_s": disc_profile.get("S", 50),
                    "disc_c": disc_profile.get("C", 50),
                    "age_min": self.instance.age_min,
                    "age_max": self.instance.age_max,
                }
            )

    def clean_target_role(self):
        value = self.cleaned_data.get("target_role", "").strip()
        if not value:
            raise forms.ValidationError("Выберите роль из списка")
        return value

    def clean(self):
        cleaned = super().clean()
        age_min = cleaned.get("age_min", 18)
        age_max = cleaned.get("age_max", 65)
        if age_min and age_max and age_min >= age_max:
            raise forms.ValidationError("Возраст «от» должен быть меньше возраста «до»")
        return cleaned

    def save(self, commit=True):
        instance = super().save(commit=False)

        instance.disc_preferred = {
            "D": self.cleaned_data.get("disc_d", 50),
            "I": self.cleaned_data.get("disc_i", 50),
            "S": self.cleaned_data.get("disc_s", 50),
            "C": self.cleaned_data.get("disc_c", 50),
        }
        instance.age_min = self.cleaned_data.get("age_min", 20)
        instance.age_max = self.cleaned_data.get("age_max", 50)
        instance.role_functions = self.cleaned_data.get("role_functions", [])
        instance.leadership_style = getattr(self.manager, "leadership_style", None) or "democratic"

        disc_profile = instance.disc_preferred
        instance.preferred_personality_types = [
            disc_type for disc_type, value in disc_profile.items() if value >= 60
        ]

        if commit:
            instance.save()
        return instance
