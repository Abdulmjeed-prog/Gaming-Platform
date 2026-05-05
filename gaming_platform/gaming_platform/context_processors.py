from commerce.models import Cart
from notifications.models import Notification


def cart_count(request):
    if not request.user.is_authenticated:
        return {'cart_count': 0}
    cart = Cart.objects.filter(user=request.user).first()
    count = cart.items.count() if cart else 0
    return {'cart_count': count}


def unread_notifications(request):
    if not request.user.is_authenticated:
        return {'unread_notifications_count': 0}
    count = Notification.objects.filter(user=request.user, is_read=False).count()
    return {'unread_notifications_count': count}