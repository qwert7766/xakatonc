from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.urls import reverse
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
    
    recommendations = get_recommendations(ideal, limit=10)
    
    for rec in recommendations:
        employee = rec['employee']
        
        
        if employee.disc_scores:
            rec['disc_d'] = employee.disc_scores.get('D', 0)
            rec['disc_i'] = employee.disc_scores.get('I', 0)
            rec['disc_s'] = employee.disc_scores.get('S', 0)
            rec['disc_c'] = employee.disc_scores.get('C', 0)
        else:
            rec['disc_d'] = rec['disc_i'] = rec['disc_s'] = rec['disc_c'] = 0
        
        # Определяем доминирующий тип DISC
        disc_values = {
            'D': rec['disc_d'],
            'I': rec['disc_i'],
            'S': rec['disc_s'],
            'C': rec['disc_c']
        }
        rec['disc_primary'] = max(disc_values, key=disc_values.get) if any(disc_values.values()) else '—'
        
        
        rec['generation_display'] = employee.get_generation_display()
        rec['gerchikov_display'] = employee.get_gerchikov_type_display()
        
        
        rec['disc_d_class'] = 'high' if rec['disc_d'] >= 60 else ''
        rec['disc_i_class'] = 'high' if rec['disc_i'] >= 60 else ''
        rec['disc_s_class'] = 'high' if rec['disc_s'] >= 60 else ''
        rec['disc_c_class'] = 'high' if rec['disc_c'] >= 60 else ''
    

    for rec in recommendations[:5]:
        RecommendationLog.objects.update_or_create(
            manager=request.user,
            ideal_profile=ideal,
            employee=rec['employee'],
            defaults={
                'match_score': rec['score'],
                'score_breakdown': rec['breakdown'],
                'status': 'good' if rec['score'] >= 70 else 'average',
            }
        )
    
    return render(request, 'recommendations/best_recommendation.html', {
        'ideal': ideal,
        'recommendations': recommendations,
    })


@login_required
def save_recommendation_status(request, profile_id, employee_id):
    """Сохраняет статус рекомендации"""
    if request.method == 'POST':
        ideal = get_object_or_404(IdealProfile, id=profile_id, manager=request.user)
        employee = get_object_or_404(Employee, id=employee_id)
        
        status = request.POST.get('status')
        comment = request.POST.get('comment', '')
        
        log, created = RecommendationLog.objects.update_or_create(
            manager=request.user,
            ideal_profile=ideal,
            employee=employee,
            defaults={
                'status': status,
                'comment': comment,
                'works_well_in_team': request.POST.get('works_well') == 'on',
                'productive': request.POST.get('productive') == 'on',
                'fits_manager_style': request.POST.get('fits_style') == 'on',
            }
        )
        
        if status == 'taken' and ideal.team:
            ideal.team.employees.add(employee)
        
        return redirect('show_recommendation', profile_id=profile_id)
    
    return redirect('show_recommendation', profile_id=profile_id)