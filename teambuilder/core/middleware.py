from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse


class RequireCompleteProfileMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, "user", None)

        if not user or not user.is_authenticated:
            return self.get_response(request)

        allowed_paths = {
            reverse("profile"),
            reverse("profile_edit"),
            reverse("profile_disc_test"),
            reverse("logout"),
        }

        if request.path.startswith("/admin/") or request.path.startswith("/join/"):
            return self.get_response(request)

        if request.path in allowed_paths:
            return self.get_response(request)

        if not getattr(user, "is_profile_complete", True):
            missing_fields = ", ".join(user.get_missing_profile_fields())
            messages.warning(
                request,
                f"Заполните профиль руководителя. Не хватает: {missing_fields}.",
            )
            return redirect("profile")

        return self.get_response(request)
