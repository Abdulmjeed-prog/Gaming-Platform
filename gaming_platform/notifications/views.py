from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponseForbidden
from games.models import Game
from library.models import UserGameLibrary
from .models import Notification
from .forms import AnnouncementForm


def owns_game(user, game):
    return game.developer_id == user.pk


@login_required
def post_announcement(request: HttpRequest, slug):
    game = get_object_or_404(Game, slug=slug)
    if not owns_game(request.user, game):
        return HttpResponseForbidden()

    if request.method == 'POST':
        form = AnnouncementForm(request.POST)
        if form.is_valid():
            title = form.cleaned_data['title']
            message = form.cleaned_data['message']
            link = request.build_absolute_uri(
                f'/games/{game.slug}/'
            )

            owners = UserGameLibrary.objects.filter(
                game=game
            ).select_related('user')

            Notification.objects.bulk_create([
                Notification(
                    user=entry.user,
                    type='announcement',
                    title=title,
                    message=message,
                    link=link,
                )
                for entry in owners
            ])

            return redirect('games:game_manage', slug=game.slug)
    else:
        form = AnnouncementForm()

    return render(request, 'notifications/post_announcement.html', {
        'form': form,
        'game': game,
    })