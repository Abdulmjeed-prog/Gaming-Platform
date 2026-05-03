from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db.models import Avg, Count
from .models import Review
from games.utils import bump_trending_score


def _update_game_rating(game):
    result = Review.objects.filter(game=game).aggregate(
        avg=Avg('rating'),
        count=Count('id'),
    )
    game.avg_rating = result['avg'] or 0
    game.rating_count = result['count']
    game.save(update_fields=['avg_rating', 'rating_count'])


@receiver(post_save, sender=Review)
def review_saved(sender, instance, created, **kwargs):
    _update_game_rating(instance.game)
    if created:
        bump_trending_score(instance.game, 1)


@receiver(post_delete, sender=Review)
def review_deleted(sender, instance, **kwargs):
    _update_game_rating(instance.game)
    bump_trending_score(instance.game, -1)