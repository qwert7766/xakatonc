from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import IdealProfileForm
from .models import IdealProfile


@login_required
def create_ideal_profile(request):
    if request.method == 'POST':
        form = IdealProfileForm(request.POST)
        if form.is_valid():
            profile = form.save(commit=False)
            profile.manager = request.user
            profile.save()
            return render(request, 'recommendations/create_profile.html', {
                'form': form,
                'title': 'Создание идеального профиля сотрудника',
                'success': f'Профиль "{profile.target_role}" успешно создан!'
            })
    else:
        form = IdealProfileForm(initial={
            'disc_preferred': {"D": 60, "I": 60, "S": 50, "C": 40},
            'age_range': {"min": 25, "max": 50},
            'preferred_personality_types': ['S', 'C'],
        })

    return render(request, 'recommendations/create_profile.html', {
        'form': form,
        'title': 'Создание идеального профиля сотрудника'
    })


@login_required
def show_recommendation(request, profile_id):
    try:
        ideal = IdealProfile.objects.get(id=profile_id, manager=request.user)
    except IdealProfile.DoesNotExist:
        return redirect('create_ideal_profile')
    
    return render(request, 'recommendations/best_recommendation.html', {
        'ideal': ideal,
        'employee': None,
        'score': None,
        'explanation': 'Функция рекомендаций временно отключена. Скоро появится!',
    })