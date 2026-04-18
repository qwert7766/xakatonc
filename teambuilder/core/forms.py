from django import forms

from .models import CustomUser


class ProfileEditForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = [
            "first_name",
            "email",
            "age",
            "generation",
            "gerchikov_type",
            "leadership_style",
        ]
        labels = {
            "first_name": "Полное имя",
            "email": "Email",
            "age": "Возраст",
            "generation": "Поколение",
            "gerchikov_type": "Тип мотивации",
            "leadership_style": "Стиль управления",
        }
