from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .models import Employee
from .forms import EmployeeRegistrationForm, DiscTestForm, TeamForm
from .models import Team, Employee


@login_required
def team_list(request):
    """Список команд руководителя"""
    teams = Team.objects.filter(manager=request.user)
    return render(request, 'profiles/team_list.html', {'teams': teams})


@login_required
def team_create(request):
    """Создание новой команды"""
    if request.method == 'POST':
        form = TeamForm(request.POST)
        if form.is_valid():
            team = form.save(commit=False)
            team.manager = request.user
            team.save()
            return redirect('team_list')
    else:
        form = TeamForm()
    
    return render(request, 'profiles/team_form.html', {
        'form': form,
        'title': 'Создание команды'
    })


@login_required
def team_detail(request, team_id):
    """Детали команды"""
    team = get_object_or_404(Team, id=team_id, manager=request.user)
    employees = team.employees.all()
    available_employees = Employee.objects.filter(is_active_candidate=True).exclude(teams=team)
    return render(request, 'profiles/team_detail.html', {
        'team': team,
        'employees': employees,
        'available_employees': available_employees,
    })


@login_required
def team_edit(request, team_id):
    """Редактирование команды"""
    team = get_object_or_404(Team, id=team_id, manager=request.user)
    
    if request.method == 'POST':
        form = TeamForm(request.POST, instance=team)
        if form.is_valid():
            form.save()
            return redirect('team_list')
    else:
        form = TeamForm(instance=team)
    
    return render(request, 'profiles/team_form.html', {
        'form': form,
        'title': 'Редактирование команды'
    })


@login_required
def team_delete(request, team_id):
    """Удаление команды"""
    team = get_object_or_404(Team, id=team_id, manager=request.user)
    
    if request.method == 'POST':
        team.delete()
        return redirect('team_list')
    
    return render(request, 'profiles/team_confirm_delete.html', {'team': team})


@login_required
def team_add_member(request, team_id):
    """Добавление сотрудника в команду"""
    team = get_object_or_404(Team, id=team_id, manager=request.user)
    
    if request.method == 'POST':
        employee_id = request.POST.get('employee_id')
        employee = get_object_or_404(Employee, id=employee_id)
        team.employees.add(employee)
        return redirect('team_detail', team_id=team.id)
    
    available_employees = Employee.objects.filter(is_active_candidate=True).exclude(teams=team)
    return render(request, 'profiles/team_add_member.html', {
        'team': team,
        'employees': available_employees
    })


@login_required
def team_remove_member(request, team_id, employee_id):
    """Удаление сотрудника из команды (без оценки)"""
    team = get_object_or_404(Team, id=team_id, manager=request.user)
    employee = get_object_or_404(Employee, id=employee_id)
    team.employees.remove(employee)
    messages.info(request, f'{employee.fio} удалён из команды')
    return redirect('team_detail', team_id=team.id)


@login_required
def team_remove_member_with_rating(request, team_id, employee_id):
    """Удаление сотрудника из команды с оценкой"""
    team = get_object_or_404(Team, id=team_id, manager=request.user)
    employee = get_object_or_404(Employee, id=employee_id)
    
    if request.method == 'POST':
        rating = request.POST.get('rating', 0)
        reject_reason = request.POST.get('reject_reason', '')
        comment = request.POST.get('comment', '')
        
        from recommendations.models import RecommendationLog
        
        full_comment = f"Оценка: {rating}/5. Причина: {reject_reason}. {comment}"
        
        # Создаем новую запись без ideal_profile (теперь поле может быть пустым)
        RecommendationLog.objects.create(
            manager=request.user,
            employee=employee,
            status='rejected',
            comment=full_comment,
            match_score=0
        )
        
        messages.info(request, f'{employee.fio} удалён из команды (оценка {rating}/5)')
    
    team.employees.remove(employee)
    return redirect('team_detail', team_id=team.id)


def onboarding_start(request):
    """Форма сотрудника"""
    if request.method == 'POST':
        form = EmployeeRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            employee = form.created_employee
            request.session['onboarding_employee_id'] = employee.id
            return redirect('onboarding_disc')
    else:
        form = EmployeeRegistrationForm()

    return render(request, 'profiles/employee_registration.html', {'form': form})


def onboarding_disc(request):
    """DISC-тест."""
    employee_id = request.session.get('onboarding_employee_id')
    if not employee_id:
        return redirect('onboarding')

    employee = get_object_or_404(Employee, id=employee_id)

    if request.method == 'POST':
        form = DiscTestForm(request.POST)
        if form.is_valid():
            employee.disc_scores = form.calculate_scores()
            employee.save()
            request.session.pop('onboarding_employee_id', None)
            request.session['onboarding_done_id'] = employee.id
            return redirect('onboarding_complete')
    else:
        form = DiscTestForm()

    return render(request, 'profiles/disc_test.html', {
        'form': form,
        'employee': employee,
    })


def onboarding_complete(request):
    """Страница завершения."""
    employee_id = request.session.get('onboarding_done_id')
    if not employee_id:
        return redirect('onboarding')

    employee     = get_object_or_404(Employee, id=employee_id)
    scores       = employee.disc_scores or {}
    primary_type = max(scores, key=scores.get) if scores else '—'

    return render(request, 'profiles/onboarding_complete.html', {
        'employee':     employee,
        'scores':       scores,
        'primary_type': primary_type,
    })