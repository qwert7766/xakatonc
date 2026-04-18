from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .forms import ProfileEditForm
from profiles.forms import DiscTestForm

@login_required
def profile_view(request):
    user = request.user
    return render(request, 'profile.html', {'user': user})


@login_required
def profile_edit_view(request):
    if request.method == "POST":
        form = ProfileEditForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect("profile")
    else:
        form = ProfileEditForm(instance=request.user)

    return render(request, "profile_edit.html", {"form": form})


@login_required
def profile_disc_test_view(request):
    if request.method == "POST":
        form = DiscTestForm(request.POST)
        if form.is_valid():
            request.user.disc_profile = form.calculate_scores()
            request.user.save(update_fields=["disc_profile"])
            return redirect("profile")
    else:
        form = DiscTestForm()

    return render(request, "profile_disc_test.html", {"form": form})


def logout_view(request):
    logout(request)
    return redirect("login")

@login_required
def home_view(request):
    teams = request.user.teams.all() if request.user.is_authenticated else []
    return render(request, 'home.html', {'teams': teams})
