from django.utils import timezone
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from games.models import Game, GameKey
from .models import Cart, CartItem, Order, OrderItem, PaymentMethod, StripeCustomer
import stripe
from django.conf import settings
from django.http import HttpRequest, HttpResponse
from decimal import Decimal
from django.contrib import messages
from django.db import transaction
from django.db.models import F
from django.utils import timezone
from library.models import UserGameLibrary
from analytics.models import GameAnalytics,DeveloperEarnings
from accounts.models import DeveloperProfile
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags


stripe.api_key = settings.STRIPE_SECRET_KEY


def commerce_view(request):
    return render(request, 'commerce/commerce.html')


@login_required
def add_to_cart(request, game_id):
    if request.user.groups.filter(name='Developer').exists():
        messages.warning(request, 'You are not allowed.')
        return redirect('main:home_view')

    game = get_object_or_404(Game, id=game_id)

    already_owned = UserGameLibrary.objects.filter(
        user=request.user,
        game=game,
        is_active=True
    ).exists()

    if already_owned:
        messages.warning(request, 'You already own this game.')
        return redirect('games:game_detail', slug=game.slug)

    try:
        quantity = int(request.POST.get('quantity', 1))
        if quantity < 1:
            quantity = 1
    except (TypeError, ValueError):
        quantity = 1

    if game.platform == Game.PlatformChoices.WEB:
        quantity = 1

    cart, created = Cart.objects.get_or_create(user=request.user)

    cart_item, item_created = CartItem.objects.get_or_create(
        cart=cart,
        game=game,
        defaults={
            'price': game.price,
            'quantity': quantity
        }
    )

    if not item_created:
        if game.platform == Game.PlatformChoices.WEB:
            messages.info(request, 'Web games can only have quantity 1.')
            return redirect('commerce:cart_view')

        cart_item.quantity += quantity
        cart_item.save()

    messages.success(request, f'{game.title} added to cart.')
    return redirect('commerce:cart_view')


@login_required
def cart_view(request: HttpRequest):
    if request.user.groups.filter(name='Developer').exists():
        messages.warning(request,'You are not allowed')
        return redirect('main:home_view')
    cart = Cart.objects.filter(user=request.user).first()
    items = cart.items.all() if cart else []
    total = sum(item.price * item.quantity for item in items)

    return render(request, 'commerce/cart.html', {
        'items': items,
        'total': total,
    })


from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect

from library.models import UserGameLibrary
from .models import CartItem
from games.models import Game


@login_required
def increase_quantity(request, item_id):
    if request.method == 'POST':
        item = get_object_or_404(
            CartItem,
            id=item_id,
            cart__user=request.user
        )

        already_owned = UserGameLibrary.objects.filter(
            user=request.user,
            game=item.game,
            is_active=True
        ).exists()

        if already_owned:
            messages.warning(request, 'You already own this game.')
            item.delete()
            return redirect('commerce:cart_view')

        if item.game.platform == Game.PlatformChoices.WEB:
            messages.info(request, 'Web games can only have quantity 1.')
            item.quantity = 1
            item.save()
            return redirect('commerce:cart_view')

        item.quantity += 1
        item.save()

    return redirect('commerce:cart_view')


@login_required
def decrease_quantity(request, item_id):
    if request.method == 'POST':
        item = get_object_or_404(
            CartItem,
            id=item_id,
            cart__user=request.user
        )

        already_owned = UserGameLibrary.objects.filter(
            user=request.user,
            game=item.game,
            is_active=True
        ).exists()

        if already_owned:
            messages.warning(request, 'You already own this game.')
            item.delete()
            return redirect('commerce:cart_view')

        if item.game.platform == Game.PlatformChoices.WEB:
            item.delete()
            messages.info(request, 'Web games can only have quantity 1, so the item was removed from your cart.')
            return redirect('commerce:cart_view')

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
    if request.user.groups.filter(name='Developer').exists():
        messages.warning(request,'You are not allowed')
        return redirect('main:home_view')
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
    if request.user.groups.filter(name='Developer').exists():
        messages.warning(request,'You are not allowed')
        return redirect('main:home_view')
    cards = PaymentMethod.objects.filter(user=request.user).order_by('-is_default', '-created_at')
    return render(request, 'commerce/my_cards.html', {'cards': cards})


def _record_sale(item, today):
    # update game analytics
    analytics, _ = GameAnalytics.objects.get_or_create(
        game=item.game,
        date=today,
        defaults={'views': 0, 'purchases': 0, 'revenue': Decimal('0.00')}
    )
    GameAnalytics.objects.filter(pk=analytics.pk).update(
        purchases=F('purchases') + item.quantity,
        revenue=F('revenue') + item.price * item.quantity,
    )

    # update developer earnings
    if item.game.developer:
        try:
            dev_profile = DeveloperProfile.objects.get(user=item.game.developer)
        except DeveloperProfile.DoesNotExist:
            return

        earnings, _ = DeveloperEarnings.objects.get_or_create(
            developer=dev_profile,
            date=today,
            defaults={'revenue': Decimal('0.00')}
        )
        DeveloperEarnings.objects.filter(pk=earnings.pk).update(
            revenue=F('revenue') + item.price * item.quantity,
        )


@login_required
def checkout_view(request: HttpRequest):
    if request.user.groups.filter(name='Developer').exists():
        messages.warning(request,'You are not allowed')
        return redirect('main:home_view')
    if not request.user.is_authenticated:
        messages.error(request, 'You need to log in first.')
        return redirect('accounts:login_view')

    cart = Cart.objects.filter(user=request.user).first()

    if not cart or not cart.items.exists():
        messages.error(request, 'Your cart is empty.')
        return redirect('commerce:cart_view')

    cart_items = cart.items.select_related('game')
    total = sum(item.price * item.quantity for item in cart_items)
    saved_cards = PaymentMethod.objects.filter(user=request.user).order_by('-is_default', '-created_at')

    if request.method == 'POST':
        payment_method_id = request.POST.get('payment_method')

        if not payment_method_id:
            messages.error(request, 'Please select a card.')
            return redirect('commerce:checkout_view')

        selected_card = PaymentMethod.objects.filter(
            user=request.user,
            stripe_payment_method_id=payment_method_id
        ).first()

        if not selected_card:
            messages.error(request, 'Invalid card selected.')
            return redirect('commerce:checkout_view')

        try:
            for item in cart_items:
                if item.game.platform != Game.PlatformChoices.WEB:
                    available_keys_count = GameKey.objects.filter(
                        game=item.game,
                        is_assigned=False
                    ).count()

                    if available_keys_count < item.quantity:
                        messages.error(
                            request,
                            f"Not enough keys available for {item.game.title}."
                        )
                        return redirect('commerce:checkout_view')

            payment_intent = stripe.PaymentIntent.create(
                amount=int(total * 100),
                currency='usd',
                customer=selected_card.stripe_customer_id,
                payment_method=selected_card.stripe_payment_method_id,
                off_session=True,
                confirm=True,
            )

            today = timezone.now().date()

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

                    if item.game.platform == Game.PlatformChoices.WEB:
                        UserGameLibrary.objects.get_or_create(
                            user=request.user,
                            game=item.game,
                            defaults={
                                'source': 'purchase',
                                'is_active': True,
                            }
                        )
                    else:
                        available_keys = GameKey.objects.filter(
                            game=item.game,
                            is_assigned=False
                        ).order_by('id')[:item.quantity]

                        if available_keys.count() < item.quantity:
                            raise ValueError(f"Not enough keys available for {item.game.title}")

                        for game_key in available_keys:
                            game_key.user = request.user
                            game_key.order = order
                            game_key.is_assigned = True
                            game_key.assigned_at = timezone.now()
                            game_key.save()

                    _record_sale(item, today)

                cart.items.all().delete()
                try:
                    send_order_confirmation_email(request, order)
                except:
                    pass
            messages.success(request, 'Payment completed successfully.')
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
            return redirect('commerce:checkout_view')

        except Exception as e:
            messages.error(request, f"Something went wrong: {str(e)}")
            return redirect('commerce:checkout_view')

    return render(request, 'commerce/checkout.html', {
        'items': cart_items,
        'total': total,
        'saved_cards': saved_cards,
    })


@login_required
def order_success(request, order_id):
    if request.user.groups.filter(name='Developer').exists():
        messages.warning(request,'You are not allowed')
        return redirect('main:home_view')
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'commerce/order_success.html', {'order': order})
    
def send_order_confirmation_email(request, order):
    subject = f"Order Confirmation #{order.id}"

    html_message = render_to_string('commerce/emails/order_confirmation.html', {
        'user': request.user,
        'order': order,
    })
    plain_message = strip_tags(html_message)

    send_mail(
        subject=subject,
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[request.user.email],
        html_message=html_message,
        fail_silently=False,
    )




