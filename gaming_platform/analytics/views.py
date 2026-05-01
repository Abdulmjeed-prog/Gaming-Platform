from django.shortcuts import get_object_or_404, render
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponseForbidden
from django.db.models import Sum, Count, Avg
from games.models import Game
from commerce.models import OrderItem
from library.models import UserGameProgress
from social.models import Review


def owns_game(user, game):
    return game.developer_id == user.pk


@login_required
def game_analytics(request: HttpRequest, slug):
    game = get_object_or_404(Game, slug=slug)
    if not owns_game(request.user, game):
        return HttpResponseForbidden()

    sales = OrderItem.objects.filter(
        game=game,
        order__status='completed',
    ).aggregate(
        total_revenue=Sum('price'),
        total_units=Count('id'),
    )

    engagement = UserGameProgress.objects.filter(
        game=game,
    ).aggregate(
        total_players=Count('user', distinct=True),
        total_playtime=Sum('playtime_seconds'),
    )

    rating_data = Review.objects.filter(
        game=game,
    ).aggregate(
        avg_rating=Avg('rating'),
        total_reviews=Count('id'),
    )

    recent_reviews = Review.objects.filter(
        game=game,
    ).select_related('user').order_by('-created_at')[:5]

    return render(request, 'analytics/game_analytics.html', {
        'game': game,
        'sales': sales,
        'engagement': engagement,
        'rating_data': rating_data,
        'recent_reviews': recent_reviews,
    })