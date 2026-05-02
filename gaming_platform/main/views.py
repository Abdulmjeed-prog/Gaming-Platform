from django.shortcuts import render, redirect
from django.http import HttpRequest, HttpResponse
from games.models import Game, Genre

def home_view(request: HttpRequest):
    featured_games = (
        Game.objects
        .filter(is_active=True)
        .select_related('developer')
        .prefetch_related('genre')
        .order_by('-created_at')[:4]
    )

    latest_games = (
        Game.objects
        .filter(is_active=True)
        .select_related('developer')
        .prefetch_related('genre')
        .order_by('-created_at')[:8]
    )

    genres = Genre.objects.all().order_by('name')[:6]

    context = {
        'featured_games': featured_games,
        'latest_games': latest_games,
        'genres': genres,
    }
    return render(request, 'main/home.html', context)
