from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Order
from games.utils import bump_trending_score


@receiver(post_save, sender=Order)
def order_paid(sender, instance, created, **kwargs):
    if instance.status != 'paid':
        return
    for item in instance.items.select_related('game'):
        bump_trending_score(item.game, 3 * item.quantity)