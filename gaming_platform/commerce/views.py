from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from games.models import Game
from .models import Cart, CartItem,Order, OrderItem, PaymentMethod, StripeCustomer
import stripe
from django.conf import settings
from django.http import HttpRequest, HttpResponse
from decimal import Decimal
from django.contrib import messages
from django.db import transaction
from library.models import UserGameLibrary

stripe.api_key = settings.STRIPE_SECRET_KEY

# Create your views here.

def commerce_view(request):
    # Logic for the view
    return render(request, 'commerce/commerce.html')


@login_required
def add_to_cart(request, game_id):
    game = get_object_or_404(Game, id=game_id)

    try:
        quantity = int(request.POST.get('quantity', 1))
        if quantity < 1:
            quantity = 1
    except (TypeError, ValueError):
        quantity = 1

    cart, created = Cart.objects.get_or_create(user=request.user)

    cart_item, item_created = CartItem.objects.get_or_create(
        cart=cart,
        game=game,
        defaults={'price': game.price, 'quantity': quantity}
    )

    if not item_created:
        cart_item.quantity += quantity
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

@login_required
def checkout_view(request: HttpRequest):
    cart = Cart.objects.filter(user=request.user).first()

    if not cart or not cart.items.exists():
        return redirect('commerce:cart_view')

    cart_items = cart.items.all()
    total = sum(item.price * item.quantity for item in cart_items)

    if request.method == 'POST':
        order = Order.objects.create(
            user=request.user,
            total_amount=total,
            status='pending',
            payment_method='Cash on Delivery',
            transaction_id=''
        )

        for item in cart_items:
            OrderItem.objects.create(
                order=order,
                game=item.game,
                price=item.price,
                quantity=item.quantity
            )

        cart.items.all().delete()

        return redirect('commerce:order_success', order_id=order.id)

    return render(request, 'commerce/checkout.html', {
        'items': cart_items,
        'total': total,
    })


def get_or_create_stripe_customer(user):
    customer_obj, created = StripeCustomer.objects.get_or_create(user=user)

    if customer_obj.stripe_customer_id:
        return customer_obj.stripe_customer_id

    customer = stripe.Customer.create(
        email=user.email,
        name=user.username
    )
    customer_obj.stripe_customer_id = customer.id
    customer_obj.save()
    return customer.id


@login_required
def add_card_view(request):
    stripe_customer_id = get_or_create_stripe_customer(request.user)

    setup_intent = stripe.SetupIntent.create(
        customer=stripe_customer_id,
        payment_method_types=['card'],
        usage='off_session'
    )

    return render(request, 'commerce/add_card.html', {
        'client_secret': setup_intent.client_secret,
        'stripe_publishable_key': settings.STRIPE_PUBLISHABLE_KEY,
    })


@login_required
def save_card_success(request):
    setup_intent_id = request.GET.get('setup_intent')

    if not setup_intent_id:
        return redirect('commerce:add_card')

    setup_intent = stripe.SetupIntent.retrieve(setup_intent_id)

    payment_method_id = setup_intent.payment_method
    stripe_customer_id = setup_intent.customer

    payment_method = stripe.PaymentMethod.retrieve(payment_method_id)

    obj, created = PaymentMethod.objects.get_or_create(
        stripe_payment_method_id=payment_method_id,
        defaults={
            'user': request.user,
            'stripe_customer_id': stripe_customer_id,
            'brand': payment_method.card.brand,
            'last4': payment_method.card.last4,
            'exp_month': payment_method.card.exp_month,
            'exp_year': payment_method.card.exp_year,
            'is_default': not PaymentMethod.objects.filter(user=request.user).exists(),
        }
    )

    return redirect('commerce:my_cards')


@login_required
def my_cards_view(request):
    cards = PaymentMethod.objects.filter(user=request.user).order_by('-is_default', '-created_at')
    return render(request, 'commerce/my_cards.html', {'cards': cards})




@login_required
@login_required
def checkout_view(request: HttpRequest):
    cart = Cart.objects.filter(user=request.user).first()

    if not cart or not cart.items.exists():
        return redirect('commerce:cart_view')

    cart_items = cart.items.all()
    total = sum(item.price * item.quantity for item in cart_items)
    saved_cards = PaymentMethod.objects.filter(user=request.user).order_by('-is_default', '-created_at')

    if request.method == 'POST':
        payment_method_id = request.POST.get('payment_method')

        if not payment_method_id:
            messages.error(request, 'Please select a card.')
            return redirect('commerce:checkout')

        selected_card = PaymentMethod.objects.filter(
            user=request.user,
            stripe_payment_method_id=payment_method_id
        ).first()

        if not selected_card:
            messages.error(request, 'Invalid card selected.')
            return redirect('commerce:checkout')

        try:
            payment_intent = stripe.PaymentIntent.create(
                amount=int(total * 100),
                currency='usd',
                customer=selected_card.stripe_customer_id,
                payment_method=selected_card.stripe_payment_method_id,
                off_session=True,
                confirm=True,
            )

            with transaction.atomic():
                order = Order.objects.create(
                    user=request.user,
                    total_amount=total,
                    status='paid',
                    payment_method=f"{selected_card.brand} **** {selected_card.last4}",
                    transaction_id=payment_intent.id
                )

                for item in cart_items:
                    OrderItem.objects.create(
                        order=order,
                        game=item.game,
                        price=item.price,
                        quantity=item.quantity
                    )

                    UserGameLibrary.objects.get_or_create(
                        user=request.user,
                        game=item.game,
                        defaults={
                            'source': 'purchase',
                            'is_active': True,
                        }
                    )

                cart.items.all().delete()

            return redirect('commerce:order_success', order_id=order.id)

        except stripe.error.CardError as e:
            Order.objects.create(
                user=request.user,
                total_amount=total,
                status='failed',
                payment_method=f"{selected_card.brand} **** {selected_card.last4}",
                transaction_id=''
            )
            messages.error(request, f"Payment failed: {e.user_message}")
            return redirect('commerce:checkout')

        except Exception as e:
            messages.error(request, f"Something went wrong: {str(e)}")
            return redirect('commerce:checkout')

    return render(request, 'commerce/checkout.html', {
        'items': cart_items,
        'total': total,
        'saved_cards': saved_cards,
    })

@login_required
def order_success(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'commerce/order_success.html', {'order': order})


