from django.shortcuts import render, redirect
from django.http import HttpRequest
from django.db.models import Prefetch
from games.models import Game, GameMedia
from library.models import UserGameLibrary


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

    context = {
        'hero_games': hero_games,
        'trending_games': trending_games,
        'recommended_games': recommended_games,
    }
    return render(request, 'main/home.html', context)



# views.py
from .forms import UploadTestForm

def upload_test_view(request):
    if request.method == 'POST':
        form = UploadTestForm(request.POST, request.FILES)
        print("FILES:", request.FILES)
        print("POST:", request.POST)

        if form.is_valid():
            obj = form.save()
            print("saved:", obj.id, obj.test_file.name)
            return redirect('test.html')
        else:
            print("errors:", form.errors)
    else:
        form = UploadTestForm()

    return render(request, 'main/test.html', {'form': form})