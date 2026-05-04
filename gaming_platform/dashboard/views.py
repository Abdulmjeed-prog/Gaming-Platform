from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import get_object_or_404, render, redirect
from django.db.models import Q, Sum
from django.contrib.auth.models import User, Group
from django.contrib import messages
from commerce.models import Order
from .forms import AdminAddKeyGameForm, BulkGameKeyForm
from games.models import Game, GameKey, GameMedia
from django.db import transaction
from django.core.paginator import Paginator


def is_admin(user):
    return user.is_authenticated and user.is_superuser


@login_required
@user_passes_test(is_admin)
def admin_dashboard_view(request):
    total_users = User.objects.count()
    total_games = Game.objects.count()
    total_orders = Order.objects.count()
    total_revenue = Order.objects.filter(status='completed').aggregate(
        total=Sum('total_amount')
    )['total'] or 0

    recent_orders = Order.objects.select_related('user').order_by('-id')[:5]

    context = {
        'total_users': total_users,
        'total_games': total_games,
        'total_orders': total_orders,
        'total_revenue': total_revenue,
        'recent_orders': recent_orders,
    }
    return render(request, 'dashboard/admin_dashboard.html', context)


@login_required
@user_passes_test(is_admin)
def admin_add_key_game_view(request):
    if request.method == 'POST':
        form = AdminAddKeyGameForm(request.POST, request.FILES)

        if form.is_valid():
            with transaction.atomic():
                game = form.save(commit=False)
                game.developer = request.user
                game.save()

                keys_list = form.cleaned_data.get('keys_text', [])

                existing_keys = set(
                    GameKey.objects.filter(key__in=keys_list).values_list('key', flat=True)
                )

                new_keys = [
                    GameKey(game=game, key=single_key)
                    for single_key in keys_list
                    if single_key not in existing_keys
                ]

                if new_keys:
                    GameKey.objects.bulk_create(new_keys)

                images = request.FILES.getlist('images')
                videos = request.FILES.getlist('videos')

                order_counter = 0

                for image in images:
                    GameMedia.objects.create(
                        game=game,
                        media_type='image',
                        file=image,
                        title='',
                        order=order_counter
                    )
                    order_counter += 1

                for video in videos:
                    GameMedia.objects.create(
                        game=game,
                        media_type='video',
                        file=video,
                        title='',
                        order=order_counter
                    )
                    order_counter += 1

            if existing_keys:
                messages.warning(
                    request,
                    f"{len(existing_keys)} key(s) already existed and were skipped."
                )

            messages.success(request, "Game created successfully.")
            return redirect('dashboard:admin_games_list')
    else:
        form = AdminAddKeyGameForm()

    return render(request, 'dashboard/add_key_game.html', {
        'form': form,
    })


@login_required
@user_passes_test(is_admin)
def admin_games_list_view(request):
    search_query = request.GET.get('q', '').strip()
    platform = request.GET.get('platform', '').strip()

    games = Game.objects.select_related('developer').order_by('-id')

    if search_query:
        games = games.filter(
            Q(title__icontains=search_query) |
            Q(publisher__icontains=search_query) |
            Q(developer__username__icontains=search_query)
        )

    if platform:
        games = games.filter(platform=platform)

    paginator = Paginator(games, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'selected_platform': platform,
        'platform_choices': Game.PlatformChoices.choices,
    }
    return render(request, 'dashboard/games_list.html', context)


@login_required
@user_passes_test(is_admin)
def add_game_key_view(request, slug):
    game = get_object_or_404(Game, slug=slug)

    if request.method == 'POST':
        form = BulkGameKeyForm(request.POST)
        if form.is_valid():
            keys_list = form.cleaned_data['keys_text']

            existing_keys = set(
                GameKey.objects.filter(key__in=keys_list).values_list('key', flat=True)
            )

            new_keys = [
                GameKey(game=game, key=single_key)
                for single_key in keys_list
                if single_key not in existing_keys
            ]

            with transaction.atomic():
                if new_keys:
                    GameKey.objects.bulk_create(new_keys)

            if existing_keys:
                messages.warning(
                    request,
                    f"{len(existing_keys)} key(s) already existed and were skipped."
                )

            if new_keys:
                messages.success(
                    request,
                    f"{len(new_keys)} game key(s) added successfully."
                )
            else:
                messages.info(
                    request,
                    "No new keys were added."
                )

            return redirect('dashboard:add_game_key', slug=game.slug)
    else:
        form = BulkGameKeyForm()

    return render(request, 'dashboard/more_key.html', {
        'game': game,
        'form': form,
    })

@login_required
@user_passes_test(is_admin)
def admin_update_game_view(request, slug):
    game = get_object_or_404(Game, slug=slug)

    if request.method == 'POST':
        form = AdminAddKeyGameForm(request.POST, request.FILES, instance=game)
        if form.is_valid():
            updated_game = form.save(commit=False)
            updated_game.developer = game.developer
            updated_game.save()

            messages.success(request, "Game updated successfully.")
            return redirect('dashboard:admin_games_list')
    else:
        form = AdminAddKeyGameForm(instance=game)

    return render(request, 'dashboard/update_game.html', {
        'form': form,
        'game': game,
    })




