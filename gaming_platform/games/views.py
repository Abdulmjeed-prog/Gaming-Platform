from django.shortcuts import get_object_or_404, render, redirect
import os
import zipfile
from django.conf import settings
from django.shortcuts import render, redirect
from .models import Game,Genre
from django.http import HttpRequest, HttpResponse
from .forms import GameForm
# Create your views here.

def create_game(request: HttpRequest):
    if request.method == 'POST':
        game_form = GameForm(request.POST, request.FILES)

        if game_form.is_valid():
            game = game_form.save()

            if game.game_zip:
                extract_folder = os.path.join(settings.MEDIA_ROOT, 'games', game.slug)
                os.makedirs(extract_folder, exist_ok=True)

                with zipfile.ZipFile(game.game_zip.path, 'r') as zip_ref:
                    zip_ref.extractall(extract_folder)

                for root, dirs, files in os.walk(extract_folder):
                    if 'index.html' in files:
                        full_path = os.path.join(root, 'index.html')
                        relative_path = os.path.relpath(full_path, settings.MEDIA_ROOT)
                        game.launch_file = relative_path.replace("\\", "/")
                        game.save()
                        break

            return redirect('games:game_detail', slug=game.slug)

    else:
        game_form = GameForm()

    return render(request, 'games/create_game.html', {'game_form': game_form})


def game_detail(request:HttpRequest, slug):
    game = get_object_or_404(Game, slug=slug)
    return render(request, 'games/game_detail.html', {'game': game})

def all_games(request:HttpRequest):
    games = Game.objects.all()
    return render(request, 'games/all_games.html',{'games': games})
