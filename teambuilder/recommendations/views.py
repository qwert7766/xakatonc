from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import IdealProfileForm
from .models import IdealProfile, RecommendationLog
from .scorer import get_recommendations
from profiles.models import Employee
 
 
@login_required
def create_ideal_profile(request):
    if request.method == 'POST':
        form = IdealProfileForm(request.POST, manager=request.user)
        if form.is_valid():
            profile = form.save(commit=False)
            profile.manager = request.user
            profile.save()
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
 
 
def _enrich_candidate(rec):
    """
    Добавляет в dict рекомендации поля которые ждёт шаблон:
      disc_d/i/s/c         — значения DISC сотрудника
      breakdown            — проценты по осям под старые ключи шаблона
      generation_display   — читаемое поколение
      gerchikov_display    — читаемая мотивация
    """
    employee = rec['employee']
    axes     = rec.get('axes', {})
    disc     = employee.disc_scores or {}
 
    rec['disc_d'] = disc.get('D', 0)
    rec['disc_i'] = disc.get('I', 0)
    rec['disc_s'] = disc.get('S', 0)
    rec['disc_c'] = disc.get('C', 0)
 
    rec['breakdown'] = {
        'disc':           round(axes.get('disc_fit',       0) * 100, 1),
        'role_functions': round(axes.get('motivation_fit', 0) * 100, 1),
        'gerchikov':      round(axes.get('gerchikov_pref', 0) * 100, 1),
        'age':            round(axes.get('age_fit',        0) * 100, 1),
        'generation':     round(axes.get('gen_style_fit',  0) * 100, 1),
    }
 
    rec['generation_display'] = employee.get_generation_display() if employee.generation else '—'
    rec['gerchikov_display']  = employee.get_gerchikov_type_display() if employee.gerchikov_type else '—'
 
    rec['score'] = rec.get('total', 0)
 
    return rec
 
 
@login_required
def show_recommendation(request, profile_id):
    ideal = get_object_or_404(IdealProfile, id=profile_id, manager=request.user)
 
    processed_ids = set(
        RecommendationLog.objects.filter(
            manager=request.user,
            ideal_profile=ideal
        ).values_list('employee_id', flat=True)
    )
 
    pending_ids = set(request.session.get(f'pending_candidates_{profile_id}', []))
    processed_ids.update(pending_ids)
 
    all_recommendations = get_recommendations(ideal, limit=50)
 
    top_candidate = None
    for rec in all_recommendations:
        if rec['employee'].id not in processed_ids:
            top_candidate = _enrich_candidate(rec)
            break
 
    pending_candidates = Employee.objects.filter(id__in=pending_ids) if pending_ids else []
 
    return render(request, 'recommendations/best_recommendation.html', {
        'ideal':              ideal,
        'top_candidate':      top_candidate,
        'pending_candidates': pending_candidates,
        'all_count':          len(all_recommendations),
        'reviewed_count':     len(processed_ids),
    })
 
 
@login_required
def hire_employee(request, profile_id, employee_id):
    ideal    = get_object_or_404(IdealProfile, id=profile_id, manager=request.user)
    employee = get_object_or_404(Employee, id=employee_id)
 
    all_recs = get_recommendations(ideal, limit=50)
    score = next((r['total'] for r in all_recs if r['employee'].id == employee_id), 0)
 
    RecommendationLog.objects.update_or_create(
        manager=request.user,
        ideal_profile=ideal,
        employee=employee,
        defaults={
            'match_score': score,
            'status':      'taken',
            'comment':     'Нанят по рекомендации',
        }
    )
 
    if ideal.team:
        ideal.team.employees.add(employee)
 
    pending_ids = request.session.get(f'pending_candidates_{profile_id}', [])
    if employee.id in pending_ids:
        pending_ids.remove(employee.id)
        request.session[f'pending_candidates_{profile_id}'] = pending_ids
 
    messages.success(request, f'{employee.fio} нанят!')
    return redirect('show_recommendation', profile_id=profile_id)
 
 
@login_required
def reject_employee(request, profile_id, employee_id):
    ideal    = get_object_or_404(IdealProfile, id=profile_id, manager=request.user)
    employee = get_object_or_404(Employee, id=employee_id)
 
    RecommendationLog.objects.update_or_create(
        manager=request.user,
        ideal_profile=ideal,
        employee=employee,
        defaults={'match_score': 0, 'status': 'rejected', 'comment': 'Отклонён'}
    )
 
    messages.info(request, f'{employee.fio} отклонён')
    return redirect('show_recommendation', profile_id=profile_id)
 
 
@login_required
def postpone_employee(request, profile_id, employee_id):
    employee    = get_object_or_404(Employee, id=employee_id)
    pending_ids = request.session.get(f'pending_candidates_{profile_id}', [])
 
    if employee_id not in pending_ids:
        pending_ids.append(employee_id)
        request.session[f'pending_candidates_{profile_id}'] = pending_ids
        messages.info(request, f'{employee.fio} отложен')
    else:
        messages.warning(request, f'{employee.fio} уже в отложенных')
 
    return redirect('show_recommendation', profile_id=profile_id)
 
 
@login_required
def remove_from_pending(request, profile_id, employee_id):
    pending_ids = request.session.get(f'pending_candidates_{profile_id}', [])
 
    if employee_id in pending_ids:
        pending_ids.remove(employee_id)
        request.session[f'pending_candidates_{profile_id}'] = pending_ids
        messages.success(request, 'Удалён из отложенных')
 
    return redirect('show_recommendation', profile_id=profile_id)