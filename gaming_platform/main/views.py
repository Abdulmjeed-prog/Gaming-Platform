from django.shortcuts import render, redirect
from django.http import HttpRequest
from games.models import Game, Genre


def home_view(request: HttpRequest):
    hero_games = (
        Game.objects
        .filter(is_active=True, is_featured=True)
        .prefetch_related('genre')
        .order_by('-created_at')[:6]
    )

    trending_games = (
        Game.objects
        .filter(is_active=True)
        .prefetch_related('genre')
        .order_by('-trending_score', '-avg_rating')[:6]
    )

    context = {
        'hero_games': hero_games,
        'trending_games': trending_games,
    }
    return render(request, 'main/home.html', context)