from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import IdealProfileForm
from .models import IdealProfile, RecommendationLog
from .scorer import get_recommendations, EmployeeScorer
from profiles.models import Employee


@login_required
def create_ideal_profile(request):
    if request.method == 'POST':
        form = IdealProfileForm(request.POST, manager=request.user)
        if form.is_valid():
            profile = form.save(commit=False)
            profile.manager = request.user
            profile.save()
            form.save_m2m()
            return redirect('show_recommendation', profile_id=profile.id)
    else:
        form = IdealProfileForm(manager=request.user, initial={
            'disc_d': 60, 'disc_i': 60, 'disc_s': 50, 'disc_c': 40,
            'age_min': 25, 'age_max': 50,
        })
    
    return render(request, 'recommendations/create_profile.html', {
        'form': form,
        'title': 'Создание идеального профиля сотрудника'
    })


@login_required
def show_recommendation(request, profile_id):
    ideal = get_object_or_404(IdealProfile, id=profile_id, manager=request.user)
    
    # Получаем ID уже обработанных
    processed_ids = set(
        RecommendationLog.objects.filter(
            manager=request.user,
            ideal_profile=ideal
        ).values_list('employee_id', flat=True)
    )
    
    pending_ids = set(request.session.get(f'pending_candidates_{profile_id}', []))
    processed_ids.update(pending_ids)
    
    all_recommendations = get_recommendations(ideal, limit=10)
    
    top_candidate = None
    for rec in all_recommendations:
        if rec['employee'].id not in processed_ids:
            top_candidate = rec
            break
    
    pending_candidates = Employee.objects.filter(id__in=pending_ids) if pending_ids else []
    
    if top_candidate:
        employee = top_candidate['employee']
        
        if employee.disc_scores:
            top_candidate['disc_d'] = employee.disc_scores.get('D', 0)
            top_candidate['disc_i'] = employee.disc_scores.get('I', 0)
            top_candidate['disc_s'] = employee.disc_scores.get('S', 0)
            top_candidate['disc_c'] = employee.disc_scores.get('C', 0)
        else:
            top_candidate['disc_d'] = top_candidate['disc_i'] = top_candidate['disc_s'] = top_candidate['disc_c'] = 0
        
        top_candidate['generation_display'] = employee.get_generation_display()
        top_candidate['gerchikov_display'] = employee.get_gerchikov_type_display()
    
    return render(request, 'recommendations/best_recommendation.html', {
        'ideal': ideal,
        'top_candidate': top_candidate,
        'pending_candidates': pending_candidates,
        'all_count': len(all_recommendations),
        'reviewed_count': len(processed_ids),
    })


@login_required
def hire_employee(request, profile_id, employee_id):
    ideal = get_object_or_404(IdealProfile, id=profile_id, manager=request.user)
    employee = get_object_or_404(Employee, id=employee_id)
    
    all_recommendations = get_recommendations(ideal, limit=10)
    score = 0
    for rec in all_recommendations:
        if rec['employee'].id == employee_id:
            score = rec['score']
            break
    
    RecommendationLog.objects.update_or_create(
        manager=request.user,
        ideal_profile=ideal,
        employee=employee,
        defaults={
            'match_score': score,
            'status': 'taken',
            'comment': 'Нанят по рекомендации'
        }
    )
    
    if ideal.team:
        ideal.team.employees.add(employee)
    
    pending_ids = request.session.get(f'pending_candidates_{profile_id}', [])
    if employee.id in pending_ids:
        pending_ids.remove(employee.id)
        request.session[f'pending_candidates_{profile_id}'] = pending_ids
    
    messages.success(request, f' {employee.fio} нанят!')
    return redirect('show_recommendation', profile_id=profile_id)


@login_required
def reject_employee(request, profile_id, employee_id):
    ideal = get_object_or_404(IdealProfile, id=profile_id, manager=request.user)
    employee = get_object_or_404(Employee, id=employee_id)
    
    RecommendationLog.objects.update_or_create(
        manager=request.user,
        ideal_profile=ideal,
        employee=employee,
        defaults={
            'match_score': 0,
            'status': 'rejected',
            'comment': 'Отклонен'
        }
    )
    
    messages.info(request, f' {employee.fio} отклонен')
    return redirect('show_recommendation', profile_id=profile_id)


@login_required
def postpone_employee(request, profile_id, employee_id):
    employee = get_object_or_404(Employee, id=employee_id)
    
    pending_ids = request.session.get(f'pending_candidates_{profile_id}', [])
    
    if employee_id not in pending_ids:
        pending_ids.append(employee_id)
        request.session[f'pending_candidates_{profile_id}'] = pending_ids
        messages.info(request, f' {employee.fio} отложен')
    else:
        messages.warning(request, f'{employee.fio} уже в отложенных')
    
    return redirect('show_recommendation', profile_id=profile_id)


@login_required
def remove_from_pending(request, profile_id, employee_id):
    pending_ids = request.session.get(f'pending_candidates_{profile_id}', [])
    
    if employee_id in pending_ids:
        pending_ids.remove(employee_id)
        request.session[f'pending_candidates_{profile_id}'] = pending_ids
        messages.success(request, 'Сотрудник удален из отложенных')
    
    return redirect('show_recommendation', profile_id=profile_id)