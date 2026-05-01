import zipfile
from pathlib import Path
from django.conf import settings
from django.shortcuts import get_object_or_404, render, redirect
from django.http import HttpRequest, HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from .models import Game, GameMedia, GameVersion
from .forms import GameForm, GameVersionForm


def extract_game_zip(zip_file_field, slug):
    extract_to = Path(settings.MEDIA_ROOT) / 'games' / 'extracted' / slug
    if extract_to.exists():
        return
    extract_to.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_file_field.path, 'r') as zf:
        zf.extractall(extract_to)


def is_developer(user):
    return user.groups.filter(name='developer').exists()


def owns_game(user, game):
    return game.developer_id == user.pk


@login_required
def create_game(request: HttpRequest):
    if not is_developer(request.user):
        return HttpResponseForbidden()

    if request.method == 'POST':
        game_form = GameForm(request.POST, request.FILES)
        version_form = GameVersionForm(request.POST, request.FILES)
        has_version = bool(request.POST.get('version_number'))

        game_valid = game_form.is_valid()
        version_valid = version_form.is_valid() if has_version else True

        if game_valid and version_valid:
            game = game_form.save(commit=False)
            game.developer = request.user

            req_text = game_form.cleaned_data.get('requirements_text', '')
            requirements = {}
            for line in req_text.strip().splitlines():
                if ':' in line:
                    key, val = line.split(':', 1)
                    requirements[key.strip()] = val.strip()
            game.requirements = requirements or None
            game.save()
            game_form.save_m2m()

            if has_version:
                version = version_form.save(commit=False)
                version.game = game
                version.save()
                if version.file:
                    extract_game_zip(version.file, game.slug)

            for f in request.FILES.getlist('images'):
                GameMedia.objects.create(game=game, media_type='image', file=f, title=f.name)
            for f in request.FILES.getlist('videos'):
                GameMedia.objects.create(game=game, media_type='video', file=f, title=f.name)

            return redirect('games:game_manage', slug=game.slug)
    else:
        game_form = GameForm()
        version_form = GameVersionForm()

    return render(request, 'games/create_game.html', {
        'game_form': game_form,
        'version_form': version_form,
    })


@login_required
def game_manage(request: HttpRequest, slug):
    game = get_object_or_404(Game, slug=slug)
    if not owns_game(request.user, game):
        return HttpResponseForbidden()

    versions = game.versions.order_by('-created_at')
    return render(request, 'games/game_manage.html', {
        'game': game,
        'versions': versions,
    })


@login_required
def edit_game(request: HttpRequest, slug):
    game = get_object_or_404(Game, slug=slug)
    if not owns_game(request.user, game):
        return HttpResponseForbidden()

    if request.method == 'POST':
        game_form = GameForm(request.POST, request.FILES, instance=game)
        if game_form.is_valid():
            updated = game_form.save(commit=False)
            req_text = game_form.cleaned_data.get('requirements_text', '')
            requirements = {}
            for line in req_text.strip().splitlines():
                if ':' in line:
                    key, val = line.split(':', 1)
                    requirements[key.strip()] = val.strip()
            updated.requirements = requirements or None
            updated.save()
            game_form.save_m2m()

            for f in request.FILES.getlist('images'):
                GameMedia.objects.create(game=game, media_type='image', file=f, title=f.name)
            for f in request.FILES.getlist('videos'):
                GameMedia.objects.create(game=game, media_type='video', file=f, title=f.name)

            return redirect('games:game_manage', slug=game.slug)
    else:
        req_lines = '\n'.join(
            f'{k}: {v}' for k, v in (game.requirements or {}).items()
        )
        game_form = GameForm(instance=game, initial={'requirements_text': req_lines})

    version_form = GameVersionForm()
    versions = game.versions.order_by('-created_at')
    images = game.media.filter(media_type='image')
    videos = game.media.filter(media_type='video')

    return render(request, 'games/edit_game.html', {
        'game_form': game_form,
        'version_form': version_form,
        'game': game,
        'versions': versions,
        'images': images,
        'videos': videos,
    })


@login_required
def delete_game(request: HttpRequest, slug):
    game = get_object_or_404(Game, slug=slug)
    if not owns_game(request.user, game):
        return HttpResponseForbidden()

    if request.method == 'POST':
        for media in game.media.all():
            media.file.delete(save=False)
        for version in game.versions.all():
            version.file.delete(save=False)
        if game.cover:
            game.cover.delete(save=False)
        game.delete()
        return redirect('accounts:developer_dashboard')

    return render(request, 'games/delete_game_confirm.html', {'game': game})


@login_required
def add_version(request: HttpRequest, slug):
    game = get_object_or_404(Game, slug=slug)
    if not owns_game(request.user, game):
        return HttpResponseForbidden()

    if request.method == 'POST':
        form = GameVersionForm(request.POST, request.FILES)
        if form.is_valid():
            version = form.save(commit=False)
            version.game = game
            version.save()
            if version.file:
                extract_game_zip(version.file, game.slug)

    return redirect('games:edit_game', slug=game.slug)


@login_required
def delete_media(request: HttpRequest, pk):
    media = get_object_or_404(GameMedia, pk=pk)
    if not owns_game(request.user, media.game):
        return HttpResponseForbidden()

    if request.method == 'POST':
        slug = media.game.slug
        media.file.delete(save=False)
        media.delete()
        return redirect('games:edit_game', slug=slug)

    return HttpResponseForbidden()


@login_required
def toggle_publish(request: HttpRequest, slug):
    game = get_object_or_404(Game, slug=slug)
    if not owns_game(request.user, game):
        return HttpResponseForbidden()

    if request.method == 'POST':
        game.is_active = not game.is_active
        game.save(update_fields=['is_active'])

    return redirect('games:game_manage', slug=game.slug)


@login_required
def set_active_version(request: HttpRequest, slug, version_pk):
    game = get_object_or_404(Game, slug=slug)
    if not owns_game(request.user, game):
        return HttpResponseForbidden()

    if request.method == 'POST':
        game.versions.update(is_active=False)
        get_object_or_404(GameVersion, pk=version_pk, game=game).save_as_active()

    return redirect('games:edit_game', slug=game.slug)


def game_detail(request: HttpRequest, slug):
    game = get_object_or_404(Game, slug=slug)
    images = game.media.filter(media_type='image')
    videos = game.media.filter(media_type='video')
    is_dev = request.user.is_authenticated and owns_game(request.user, game)
    return render(request, 'games/game_detail.html', {
        'game': game,
        'images': images,
        'videos': videos,
        'is_dev': is_dev,
    })


def all_games(request: HttpRequest):
    games = Game.objects.filter(is_active=True)
    return render(request, 'games/all_games.html', {'games': games})