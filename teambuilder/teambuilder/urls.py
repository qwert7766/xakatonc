from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path
from django.views.generic import TemplateView

from core.views import home_view, logout_view, profile_disc_test_view, profile_edit_view, profile_view
from profiles.views import onboarding_start, onboarding_disc, onboarding_complete
from recommendations.views import create_ideal_profile, show_recommendation
from profiles.views import (
    team_list, team_create, team_detail, team_edit, team_delete,
    team_add_member, team_remove_member
)
urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home_view, name='home'),
 
    # Авторизация руководителя
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', logout_view, name='logout'),
 
    # Кабинет руководителя
    path('profile/', profile_view, name='profile'),
    path('profile/edit/', profile_edit_view, name='profile_edit'),
    path('profile/disc/', profile_disc_test_view, name='profile_disc_test'),
 
    # Конструктор и рекомендации
    path('constructor/', create_ideal_profile, name='create_ideal_profile'),  # ← ИСПРАВЛЕНО
    path('recommendation/<int:profile_id>/', show_recommendation, name='show_recommendation'),  # ← ДОБАВЛЕНО

    # Онбординг сотрудника
    path('join/', onboarding_start, name='onboarding'),
    path('join/disc/', onboarding_disc, name='onboarding_disc'),
    path('join/done/', onboarding_complete, name='onboarding_complete'),

    #Команды 
    path('teams/', team_list, name='team_list'),
    path('teams/create/', team_create, name='team_create'),
    path('teams/<int:team_id>/', team_detail, name='team_detail'),
    path('teams/<int:team_id>/edit/', team_edit, name='team_edit'),
    path('teams/<int:team_id>/delete/', team_delete, name='team_delete'),
    path('teams/<int:team_id>/add-member/', team_add_member, name='team_add_member'),
    path('teams/<int:team_id>/remove-member/<int:employee_id>/', team_remove_member, name='team_remove_member'),
]
