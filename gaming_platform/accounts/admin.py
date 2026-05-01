from django.contrib import admin
from .models import Profile, DeveloperProfile, FollowDeveloper
# Register your models here.

class accountsAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'bio')
    search_fields = ('user__username', 'role')

admin.site.register(Profile)
admin.site.register(DeveloperProfile)
admin.site.register(FollowDeveloper)
