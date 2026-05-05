from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponseForbidden, JsonResponse
from django.views.decorators.http import require_POST
from games.models import Game
from library.models import UserGameLibrary
from accounts.models import DeveloperProfile, FollowDeveloper
from .models import Notification, DeveloperAnnouncement
from .forms import AnnouncementForm


def owns_game(user, game):
    return game.developer_id == user.pk


@login_required
def inbox_view(request: HttpRequest):
    notifications = (
        Notification.objects
        .filter(user=request.user)
        .order_by('-created_at')
    )
    unread_count = notifications.filter(is_read=False).count()

    # mark all as read on page open
    notifications.filter(is_read=False).update(is_read=True)

    return render(request, 'notifications/inbox.html', {
        'notifications': notifications,
        'unread_count': unread_count,
    })


@require_POST
@login_required
def mark_read(request: HttpRequest, pk):
    notif = get_object_or_404(Notification, pk=pk, user=request.user)
    notif.is_read = True
    notif.save(update_fields=['is_read'])
    return JsonResponse({'ok': True})


@require_POST
@login_required
def mark_all_read(request: HttpRequest):
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return redirect('notifications:inbox')


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
            link = request.build_absolute_uri(f'/games/{game.slug}/')

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


@login_required
def post_developer_announcement(request: HttpRequest, username):
    dev_profile = get_object_or_404(
        DeveloperProfile, user=request.user
    )

    if request.user.username != username:
        return HttpResponseForbidden()

    if request.method == 'POST':
        form = AnnouncementForm(request.POST)
        if form.is_valid():
            announcement = DeveloperAnnouncement.objects.create(
                developer=dev_profile,
                title=form.cleaned_data['title'],
                content=form.cleaned_data['message'],
            )

            followers = FollowDeveloper.objects.filter(
                developer=dev_profile
            ).select_related('user')

            profile_link = request.build_absolute_uri(
                f'/accounts/profile/{username}/'
            )

            Notification.objects.bulk_create([
                Notification(
                    user=f.user,
                    type='announcement',
                    title=announcement.title,
                    message=announcement.content,
                    link=profile_link,
                )
                for f in followers
            ])

            return redirect('accounts:developer_profile', username=username)

    return redirect('accounts:developer_profile', username=username)