from django.contrib import admin
from .models import Game,Genre
# Register your models here.

class GamesAdmin(admin.ModelAdmin):

    admin.site.register(Game)
    admin.site.register(Genre)