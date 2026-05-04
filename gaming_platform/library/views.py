from pathlib import Path
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpRequest, HttpResponse
from django.db.models import Prefetch
from django.conf import settings
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.static import serve as static_serve
from games.models import Game, GameVersion
from .models import UserGameLibrary, UserGameProgress
import mimetypes
from django.core.files.storage import default_storage
from django.http import FileResponse, Http404, HttpResponse


@login_required
def library_view(request):
    progress_qs = UserGameProgress.objects.filter(user=request.user)
    active_versions_qs = GameVersion.objects.filter(is_active=True)

    entries = (
        UserGameLibrary.objects.filter(user=request.user, is_active=True)
        .select_related('game')
        .prefetch_related(
            'game__genre',
            Prefetch('game__progress_entries', queryset=progress_qs, to_attr='user_progress'),
            Prefetch('game__versions', queryset=active_versions_qs, to_attr='active_versions'),
        )
    )

    games_data = []
    for entry in entries:
        progress = entry.game.user_progress
        progress_obj = progress[0] if progress else None
        is_playable = bool(entry.game.play_url or entry.game.active_versions)
        games_data.append({
            'entry': entry,
            'game': entry.game,
            'progress': progress_obj,
            'is_playable': is_playable,
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
        entry_point = (version.entry_point if version else game.launch_file) or 'index.html'
        game_url = reverse('library:serve_game_file', kwargs={'slug': slug, 'path': entry_point})

    return render(request, 'library/play_game.html', {
        'game': game,
        'game_url': game_url,
        'playtime': progress.playtime_seconds,
    })


def _exempt(response):
    del response['X-Frame-Options']
    response.xframe_options_exempt = True
    return response


# @login_required
# def serve_game_file(request: HttpRequest, slug, path):
#     game = get_object_or_404(Game, slug=slug)
#     get_object_or_404(UserGameLibrary, user=request.user, game=game, is_active=True)

#     document_root = Path(settings.MEDIA_ROOT) / 'games' / 'extracted' / slug

#     # security: block path traversal
#     try:
#         resolved = (document_root / path).resolve()
#         resolved.relative_to(document_root.resolve())
#     except (ValueError, OSError):
#         return _exempt(HttpResponse('forbidden', status=403))

#     if not resolved.exists() or not resolved.is_file():
#         return _exempt(HttpResponse(
#             f'Game file not found: {path}', status=404
#         ))

#     return _exempt(static_serve(request, path, document_root=str(document_root)))

@login_required
def serve_game_file(request: HttpRequest, slug, path):
    game = get_object_or_404(Game, slug=slug, is_active=True)
    get_object_or_404(UserGameLibrary, user=request.user, game=game, is_active=True)

    safe_path = Path(path)
    if safe_path.is_absolute() or ".." in safe_path.parts:
        return _exempt(HttpResponse("forbidden", status=403))

    storage_path = f"games/extracted/{slug}/{path}"

    if not default_storage.exists(storage_path):
        return _exempt(HttpResponse(f"Game file not found: {path}", status=404))

    content_type, encoding = mimetypes.guess_type(path)
    content_type = content_type or "application/octet-stream"

    file_obj = default_storage.open(storage_path, "rb")
    response = FileResponse(file_obj, content_type=content_type)

    if encoding:
        response["Content-Encoding"] = encoding

    return _exempt(response)


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