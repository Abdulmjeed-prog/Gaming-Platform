from django.shortcuts import get_object_or_404, render, redirect
from django.http import HttpRequest
from .models import Game, GameMedia
from .forms import GameForm, GameVersionForm


def create_game(request: HttpRequest):
    if request.method == 'POST':
        game_form = GameForm(request.POST, request.FILES)
        version_form = GameVersionForm(request.POST, request.FILES)
        has_version = bool(request.POST.get('version_number'))

        game_valid = game_form.is_valid()
        version_valid = version_form.is_valid() if has_version else True

        if game_valid and version_valid:
            game = game_form.save(commit=False)

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

            for f in request.FILES.getlist('images'):
                GameMedia.objects.create(game=game, media_type='image', file=f, title=f.name)

            for f in request.FILES.getlist('videos'):
                GameMedia.objects.create(game=game, media_type='video', file=f, title=f.name)

            return redirect('games:game_detail', slug=game.slug)
    else:
        game_form = GameForm()
        version_form = GameVersionForm()

    return render(request, 'games/create_game.html', {
        'game_form': game_form,
        'version_form': version_form,
    })


def game_detail(request: HttpRequest, slug):
    game = get_object_or_404(Game, slug=slug)
    return render(request, 'games/game_detail.html', {'game': game})


def all_games(request: HttpRequest):
    games = Game.objects.all()
    return render(request, 'games/all_games.html', {'games': games})