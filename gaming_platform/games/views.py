import shutil
import zipfile
from pathlib import Path
from django.conf import settings
from django.shortcuts import get_object_or_404, render, redirect
from django.http import HttpRequest, HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.contrib import messages
from django.core.paginator import Paginator
from .models import Game, GameMedia, GameVersion, Genre, GameKey
from .forms import GameForm, GameVersionForm, GameKeyForm
from .decorators import developer_required
from .constants import LAST_SEEN_SESSION_KEY, LAST_SEEN_MAX
from social.forms import CommentForm, ReviewForm
from social.models import Comment, Review
from django.db.models import Q, Sum


def extract_game_zip(zip_file_field, slug):
    extract_to = Path(settings.MEDIA_ROOT) / 'games' / 'extracted' / slug
    if extract_to.exists():
        shutil.rmtree(extract_to)
    extract_to.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(zip_file_field.path, 'r') as zf:
        names = [n for n in zf.namelist() if not n.startswith('__MACOSX')]
        top_dirs = {Path(n).parts[0] for n in names if Path(n).parts}

        if len(top_dirs) == 1:
            prefix = list(top_dirs)[0] + '/'
            for member in zf.infolist():
                if member.filename.startswith('__MACOSX'):
                    continue
                if member.filename.startswith(prefix):
                    member.filename = member.filename[len(prefix):]
                if member.filename:
                    zf.extract(member, extract_to)
        else:
            for member in zf.infolist():
                if not member.filename.startswith('__MACOSX'):
                    zf.extract(member, extract_to)


def owns_game(user, game):
    return game.developer_id == user.pk


def _track_last_seen(request, game_id):
    seen = request.session.get(LAST_SEEN_SESSION_KEY, [])
    if game_id in seen:
        seen.remove(game_id)
    seen.insert(0, game_id)
    request.session[LAST_SEEN_SESSION_KEY] = seen[:LAST_SEEN_MAX]
    request.session.modified = True


@developer_required
def create_game(request: HttpRequest):

    if request.method == 'POST':
        game_form = GameForm(request.POST, request.FILES)
        version_form = GameVersionForm(request.POST, request.FILES)

        has_version = bool(request.POST.get('version_number') or request.FILES.get('file'))
        game_valid = game_form.is_valid()
        version_valid = version_form.is_valid() if has_version else True

        if game_valid:
            play_url = game_form.cleaned_data.get('play_url')
            version_has_file = has_version and version_valid and version_form.cleaned_data.get('file')
            if not play_url and not version_has_file:
                game_form.add_error(None, 'Provide a Play URL or upload a game zip file.')
                game_valid = False

        if game_valid and version_valid:
            with transaction.atomic():
                game = game_form.save(commit=False)
                game.developer = request.user
                game.is_active = False
                req_text = game_form.cleaned_data.get('requirements_text', '')
                requirements = {}
                for line in req_text.strip().splitlines():
                    if ':' in line:
                        key, val = line.split(':', 1)
                        requirements[key.strip()] = val.strip()
                game.requirements = requirements or None
                game.save()
                game_form.save_m2m()

                version = None
                if has_version:
                    version = version_form.save(commit=False)
                    version.game = game
                    version.is_active = True
                    version.save()

                for f in request.FILES.getlist('images'):
                    GameMedia.objects.create(game=game, media_type='image', file=f, title=f.name)
                for f in request.FILES.getlist('videos'):
                    GameMedia.objects.create(game=game, media_type='video', file=f, title=f.name)

            if version and version.file:
                extract_game_zip(version.file, game.slug)

            messages.success(request, f'"{game.title}" created. Publish it when ready.')
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
        extracted = Path(settings.MEDIA_ROOT) / 'games' / 'extracted' / slug
        if extracted.exists():
            shutil.rmtree(extracted)
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
        version = get_object_or_404(GameVersion, pk=version_pk, game=game)
        game.versions.update(is_active=False)
        version.is_active = True
        version.save(update_fields=['is_active'])
        if version.file:
            extract_game_zip(version.file, game.slug)

    return redirect('games:edit_game', slug=game.slug)


def game_detail(request: HttpRequest, slug):
    game = get_object_or_404(Game.objects.prefetch_related('genre', 'media'), slug=slug)
    images = game.media.filter(media_type='image')
    videos = game.media.filter(media_type='video')
    is_dev = request.user.is_authenticated and owns_game(request.user, game)

    _track_last_seen(request, game.id)

    reviews = (
        Review.objects
        .filter(game=game, is_approved=True)
        .select_related('user')
        .order_by('-created_at')
    )

    comments = (
        Comment.objects
        .filter(game=game, is_approved=True, parent__isnull=True)
        .select_related('user')
        .order_by('-created_at')
    )

    is_owned = False
    if request.user.is_authenticated:
        from library.models import UserGameLibrary
        is_owned = UserGameLibrary.objects.filter(user=request.user, game=game, is_active=True).exists()

    existing_review = None
    if request.user.is_authenticated:
        existing_review = Review.objects.filter(user=request.user, game=game).first()

    review_form = ReviewForm(instance=existing_review)
    comment_form = CommentForm()

    if request.method == 'POST':
        if not request.user.is_authenticated:
            messages.error(request, 'You need to log in first.')
            return redirect('accounts:login_view')

        if 'submit_review' in request.POST:
            review_form = ReviewForm(request.POST, instance=existing_review)
            comment_form = CommentForm()

            if review_form.is_valid():
                review = review_form.save(commit=False)
                review.user = request.user
                review.game = game
                review.save()
                messages.success(request, 'Your review has been saved.')
                return redirect('games:game_detail', slug=game.slug)

        elif 'submit_comment' in request.POST:
            comment_form = CommentForm(request.POST)
            review_form = ReviewForm(instance=existing_review)

            if comment_form.is_valid():
                comment = comment_form.save(commit=False)
                comment.user = request.user
                comment.game = game
                comment.save()
                messages.success(request, 'Your comment has been added.')
                return redirect('games:game_detail', slug=game.slug)

    return render(request, 'games/game_detail.html', {
        'game': game,
        'images': images,
        'videos': videos,
        'is_dev': is_dev,
        'is_owned': is_owned,
        'reviews': reviews,
        'comments': comments,
        'review_form': review_form,
        'comment_form': comment_form,
    })


def all_games(request: HttpRequest):
    if request.user.is_authenticated and request.user.groups.filter(name='Developer').exists():
        messages.warning(request, 'You are not allowed')
        return redirect('main:home_view')

    games = Game.objects.filter(is_active=True)

    genre = request.GET.get('genre')
    sort = request.GET.get('sort')
    platform = request.GET.get('platform')
    q = request.GET.get('q')

    if q:
        games = games.filter(title__icontains=q)

    if genre:
        games = games.filter(genre__id=genre)

    if platform in ('PC', 'WEB'):
        games = games.filter(platform=platform)

    if sort == 'price_low':
        games = games.order_by('price')
    elif sort == 'price_high':
        games = games.order_by('-price')
    elif sort == 'newest':
        games = games.order_by('-release_year')
    elif sort == 'oldest':
        games = games.order_by('release_year')
    elif sort == 'rating':
        games = games.order_by('-avg_rating')
    else:
        games = games.order_by('title')

    genres = Genre.objects.all().order_by('name')

    page_number = request.GET.get('page', 1)
    paginator = Paginator(games, 6)
    games_page = paginator.get_page(page_number)

    context = {
        'games': games_page,
        'genres': genres,
        'selected_genre': genre,
        'selected_sort': sort,
        'selected_platform': platform,
        'query': q,
    }
    return render(request, 'games/all_games.html', context)


@login_required
def add_game_key_view(request, slug):
    game = get_object_or_404(Game, slug=slug)

    if request.method == 'POST':
        form = GameKeyForm(request.POST)
        if form.is_valid():
            game_key = form.save(commit=False)
            game_key.game = game
            game_key.save()
            messages.success(request, 'Game key added successfully.')
            return redirect('games:game_detail', slug=game.slug)
    else:
        form = GameKeyForm()

    return render(request, 'games/add_game_key.html', {
        'game': game,
        'form': form,
    })


def search_game(request: HttpRequest):
    query = request.GET.get('q', '').strip()
    games = Game.objects.none()

    if query:
        games = Game.objects.filter(
            Q(title__icontains=query)
        ).distinct()

    return render(request, 'games/all_games.html', {
        'query': query,
        'games': games,
    })