from django.contrib import admin

from .models import Employee, Role, Team

admin.site.register(Employee)
admin.site.register(Team)
admin.site.register(Role)
