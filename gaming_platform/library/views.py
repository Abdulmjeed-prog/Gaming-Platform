from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpRequest
from django.db.models import Prefetch
from django.conf import settings
from django.utils import timezone
from django.views.decorators.http import require_POST
from games.models import Game
from .models import UserGameLibrary, UserGameProgress


@login_required
def library_view(request):
    progress_qs = UserGameProgress.objects.filter(user=request.user)

    entries = (
        UserGameLibrary.objects.filter(user=request.user, is_active=True)
        .select_related('game')
        .prefetch_related(
            'game__genre',
            Prefetch(
                'game__progress_entries',
                queryset=progress_qs,
                to_attr='user_progress',
            ),
        )
    )

    games_data = []
    for entry in entries:
        progress = entry.game.user_progress
        progress_obj = progress[0] if progress else None
        games_data.append({
            'entry': entry,
            'game': entry.game,
            'progress': progress_obj,
        })

    return render(request, 'library/library.html', {
        'games_data': games_data,
        'total_games': len(games_data),
    })


@login_required
def play_game(request: HttpRequest, slug):
    game = get_object_or_404(Game, slug=slug, is_active=True)

    get_object_or_404(UserGameLibrary, user=request.user, game=game, is_active=True)

    progress, _ = UserGameProgress.objects.get_or_create(user=request.user, game=game)
    progress.last_played = timezone.now()
    progress.save(update_fields=['last_played'])

    if game.play_url:
        game_url = game.play_url
    else:
        version = game.versions.filter(is_active=True).order_by('-created_at').first()
        entry_point = version.entry_point if version else game.launch_file
        game_url = f"{settings.MEDIA_URL}games/extracted/{slug}/{entry_point}"

    return render(request, 'library/play_game.html', {
        'game': game,
        'game_url': game_url,
        'playtime': progress.playtime_seconds,
    })


@require_POST
@login_required
def save_progress(request: HttpRequest, slug):
    game = get_object_or_404(Game, slug=slug)
    get_object_or_404(UserGameLibrary, user=request.user, game=game, is_active=True)

    try:
        seconds = int(request.POST.get('seconds', 0))
    except (ValueError, TypeError):
        return JsonResponse({'ok': False}, status=400)

    progress, _ = UserGameProgress.objects.get_or_create(user=request.user, game=game)
    progress.playtime_seconds += seconds
    progress.save(update_fields=['playtime_seconds', 'updated_at'])

    return JsonResponse({'ok': True, 'total': progress.playtime_seconds})