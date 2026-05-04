from django.shortcuts import render
from django.http import HttpRequest
from django.db.models import Prefetch
from games.models import Game, GameMedia
from library.models import UserGameLibrary
from social.models import Review


def _video_prefetch():
    return Prefetch(
        'media',
        queryset=GameMedia.objects.filter(media_type='video').order_by('order'),
        to_attr='preview_videos',
    )


def home_view(request: HttpRequest):
    hero_games = list(
        Game.objects
        .filter(is_active=True, is_featured=True)
        .prefetch_related('genre', _video_prefetch())
        .order_by('-trending_score')[:6]
    )

    if not hero_games:
        hero_games = list(
            Game.objects
            .filter(is_active=True)
            .prefetch_related('genre', _video_prefetch())
            .order_by('-created_at')[:6]
        )

    trending_games = (
        Game.objects
        .filter(is_active=True)
        .prefetch_related('genre', _video_prefetch())
        .order_by('-trending_score', '-avg_rating')[:6]
    )

    recommended_games = None
    if request.user.is_authenticated:
        owned = (
            UserGameLibrary.objects
            .filter(user=request.user)
            .select_related('game')
            .prefetch_related('game__genre')
        )
        genre_ids = set()
        owned_ids = set()
        for entry in owned:
            owned_ids.add(entry.game_id)
            for g in entry.game.genre.all():
                genre_ids.add(g.id)

        if genre_ids:
            recommended_games = (
                Game.objects
                .filter(is_active=True, genre__id__in=genre_ids)
                .exclude(id__in=owned_ids)
                .prefetch_related('genre', _video_prefetch())
                .order_by('-avg_rating', '-trending_score')
                .distinct()[:6]
            )

    recent_reviews = (
        Review.objects
        .select_related('user', 'user__profile', 'game')
        .filter(game__is_active=True, is_approved=True)
        .order_by('?')[:6]
    )

    context = {
        'hero_games': hero_games,
        'trending_games': trending_games,
        'recommended_games': recommended_games,
        'recent_reviews': recent_reviews,
    }
    return render(request, 'main/home.html', context)