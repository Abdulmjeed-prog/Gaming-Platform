from django.db.models import F


def bump_trending_score(game, points):
    from games.models import Game
    Game.objects.filter(pk=game.pk).update(
        trending_score=F('trending_score') + points
    )
    game.refresh_from_db(fields=['trending_score'])
    refresh_featured(game)


def refresh_featured(updated_game=None):
    from games.models import Game

    featured = list(
        Game.objects
        .filter(is_featured=True, is_active=True)
        .order_by('trending_score')
        .values('id', 'trending_score')
    )

    if len(featured) < 5:
        top_ids = set(
            Game.objects
            .filter(is_active=True)
            .order_by('-trending_score')
            .values_list('id', flat=True)[:5]
        )
        Game.objects.filter(is_active=True).update(is_featured=False)
        Game.objects.filter(id__in=top_ids).update(is_featured=True)
        return

    if updated_game is None:
        return

    featured_ids = {f['id'] for f in featured}
    if updated_game.pk in featured_ids:
        return

    weakest = featured[0]
    if updated_game.trending_score > weakest['trending_score']:
        Game.objects.filter(id=weakest['id']).update(is_featured=False)
        Game.objects.filter(id=updated_game.pk).update(is_featured=True)