from commerce.models import Cart


def cart_count(request):
    if not request.user.is_authenticated:
        return {'cart_count': 0}
    cart = Cart.objects.filter(user=request.user).first()
    if not cart:
        return {'cart_count': 0}
    count = cart.items.count()
    return {'cart_count': count}