import shutil
import zipfile
from pathlib import Path
from django.conf import settings
from django.shortcuts import get_object_or_404, render, redirect
from django.http import HttpRequest, HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from .models import Game, GameMedia, GameVersion, Genre
from .forms import GameForm, GameVersionForm
from django.core.paginator import Paginator
from social.forms import CommentForm, ReviewForm
from social.models import Comment, Review
from django.contrib import messages


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


def is_developer(user):
    return user.groups.filter(name='developer').exists()


def owns_game(user, game):
    return game.developer_id == user.pk


@login_required
def create_game(request: HttpRequest):
    if not request.user.groups.filter(name='Developer').exists():
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
                version.is_active = True
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
        'reviews': reviews,
        'comments': comments,
        'review_form': review_form,
        'comment_form': comment_form,
    })



def all_games(request: HttpRequest):
    games = Game.objects.filter(is_active=True)

    genre = request.GET.get('genre')
    sort = request.GET.get('sort')

    if genre:
        games = games.filter(genre__id=genre)

    if sort == 'price_low':
        games = games.order_by('price')
    elif sort == 'price_high':
        games = games.order_by('-price')
    elif sort == 'newest':
        games = games.order_by('-release_year')
    elif sort == 'oldest':
        games = games.order_by('release_year')
    else:
        games = games.order_by('title')

    genres = Genre.objects.all().order_by('name')

    page_number = request.GET.get('page',1)
    paginator = Paginator(games,6)
    games_page = paginator.get_page(page_number)

    context = {
        'games': games_page,
        'genres': genres,
        'selected_genre': genre,
        'selected_sort': sort,
    }
    return render(request, 'games/all_games.html', context)
