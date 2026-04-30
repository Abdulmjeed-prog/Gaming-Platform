from django.shortcuts import get_object_or_404, render, redirect
import os
import zipfile
from django.conf import settings
from django.shortcuts import render, redirect
from .models import Game,Genre

# Create your views here.

def create_game(request):
    genre = Genre.objects.all()
    if request.method == 'POST':
        title = request.POST.get('title')
        zip_file = request.FILES.get('game_zip')

        game = Game.objects.create(
            title=title,
            price=0,
            publisher='Unknown',
            release_year=2026,
            platform='WEB',
            game_zip=zip_file
        )

        if game.game_zip:
            extract_folder = os.path.join(settings.MEDIA_ROOT, 'games', game.slug)
            os.makedirs(extract_folder, exist_ok=True)

            with zipfile.ZipFile(game.game_zip.path, 'r') as zip_ref:
                zip_ref.extractall(extract_folder)

            game.launch_file = f'games/{game.slug}/index.html'
            game.save()

        return redirect('games:game_detail', slug=game.slug)

    return render(request, 'games/create_game.html',{'genres': genre})


def game_detail(request, slug):
    game = get_object_or_404(Game, slug=slug)
    return render(request, 'games/game_detail.html', {'game': game})
