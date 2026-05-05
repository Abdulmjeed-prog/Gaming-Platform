from django.shortcuts import render, redirect
from django.http import HttpRequest
from django.db.models import Prefetch, Count, Sum, Q, DecimalField, Value
from django.db.models.functions import Coalesce
from games.models import Game, GameMedia
from library.models import UserGameLibrary
from social.models import Review

LAST_SEEN_SESSION_KEY = 'last_seen'


def _video_prefetch():
    return Prefetch(
        'media',
        queryset=GameMedia.objects.filter(media_type='video').order_by('order'),
        to_attr='preview_videos',
    )


def get_bestsellers():
    from commerce.models import OrderItem
    paid = Q(orderitem__order__status='paid')
    return (
        Game.objects
        .filter(is_active=True)
        .annotate(
            units_sold=Count('orderitem', filter=paid, distinct=True),
            total_revenue=Coalesce(
                Sum('orderitem__price', filter=paid),
                Value(0, output_field=DecimalField(max_digits=12, decimal_places=2))
            )
        )
        .prefetch_related('genre', _video_prefetch())
        .order_by('-total_revenue', '-price')[:5]
    )


def get_last_seen(request):
    seen_ids = request.session.get(LAST_SEEN_SESSION_KEY, [])
    if not seen_ids:
        return []
    games = (
        Game.objects
        .filter(id__in=seen_ids, is_active=True)
        .prefetch_related('genre', _video_prefetch())
    )
    games_map = {g.id: g for g in games}
    return [games_map[gid] for gid in seen_ids if gid in games_map]


def home_view(request: HttpRequest):
    if request.user.is_authenticated and request.user.groups.filter(name='Developer').exists():
        return redirect('accounts:developer_dashboard')

    hero_games = list(
        Game.objects
        .filter(is_active=True, is_featured=True)
        .prefetch_related('genre', _video_prefetch())
        .order_by('-trending_score')[:6]
    )

    if not hero_games:
        hero_games = list(
            Game.objects
            .filter(is_active=True)
            .prefetch_related('genre', _video_prefetch())
            .order_by('-created_at')[:6]
        )

    trending_games = (
        Game.objects
        .filter(is_active=True)
        .prefetch_related('genre', _video_prefetch())
        .order_by('-trending_score', '-avg_rating')[:6]
    )

    recommended_games = None
    if request.user.is_authenticated:
        owned = (
            UserGameLibrary.objects
            .filter(user=request.user)
            .select_related('game')
            .prefetch_related('game__genre')
        )
        genre_ids = set()
        owned_ids = set()
        for entry in owned:
            owned_ids.add(entry.game_id)
            for g in entry.game.genre.all():
                genre_ids.add(g.id)

        if genre_ids:
            recommended_games = (
                Game.objects
                .filter(is_active=True, genre__id__in=genre_ids)
                .exclude(id__in=owned_ids)
                .prefetch_related('genre', _video_prefetch())
                .order_by('-avg_rating', '-trending_score')
                .distinct()[:6]
            )

    recent_reviews = (
        Review.objects
        .select_related('user', 'user__profile', 'game')
        .filter(game__is_active=True, is_approved=True)
        .order_by('?')[:6]
    )

    bestsellers = list(get_bestsellers())
    last_seen = get_last_seen(request)

    context = {
        'hero_games': hero_games,
        'trending_games': trending_games,
        'recommended_games': recommended_games,
        'recent_reviews': recent_reviews,
        'bestsellers': bestsellers,
        'last_seen': last_seen,
    }
    return render(request, 'main/home.html', context)



# views.py
from .forms import UploadTestForm

def upload_test_view(request):
    if request.method == 'POST':
        form = UploadTestForm(request.POST, request.FILES)
        print("FILES:", request.FILES)
        print("POST:", request.POST)

        if form.is_valid():
            obj = form.save()
            print("saved:", obj.id, obj.test_file.name)
            return redirect('test.html')
        else:
            print("errors:", form.errors)
    else:
        form = UploadTestForm()

    return render(request, 'main/test.html', {'form': form})