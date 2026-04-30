from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from games.models import Game
from .models import Cart, CartItem
from django.http import HttpRequest, HttpResponse


# Create your views here.

def commerce_view(request):
    # Logic for the view
    return render(request, 'commerce/commerce.html')


@login_required
def add_to_cart(request, game_id):
    game = get_object_or_404(Game, id=game_id)

    cart, created = Cart.objects.get_or_create(user=request.user)

    cart_item, item_created = CartItem.objects.get_or_create(
        cart=cart,
        game=game,
        defaults={'price': game.price, 'quantity': 1}
    )

    if not item_created:
        cart_item.quantity += 1
        cart_item.save()

    return redirect('commerce:cart_view')


def cart_view(request: HttpRequest):
    cart = Cart.objects.filter(user=request.user).first()
    items = cart.items.all() if cart else []
    total = sum(item.price * item.quantity for item in items)

    return render(request, 'commerce/cart.html', {
        'items': items,
        'total': total,
    })


@login_required
def increase_quantity(request, item_id):
    if request.method == 'POST':
        item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
        item.quantity += 1
        item.save()

    return redirect('commerce:cart_view')


@login_required
def decrease_quantity(request, item_id):
    if request.method == 'POST':
        item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)

        if item.quantity > 1:
            item.quantity -= 1
            item.save()
        else:
            item.delete()

    return redirect('commerce:cart_view')


@login_required
def remove_from_cart(request, item_id):
    if request.method == 'POST':
        item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
        item.delete()

    return redirect('commerce:cart_view')
