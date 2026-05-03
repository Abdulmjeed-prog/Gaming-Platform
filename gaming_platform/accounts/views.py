from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpRequest, HttpResponseForbidden, JsonResponse
from django.contrib.auth.models import Group, User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Sum

from .forms import ProfileForm, CustomUserCreationForm, CustomUserUpdateForm, DeveloperProfileForm
from .models import Profile, DeveloperProfile, FollowDeveloper
from notifications.forms import AnnouncementForm
from commerce.models import Order
from django.utils.html import strip_tags
from django.template.loader import render_to_string
from django.core.mail import send_mail
from django.conf import settings

def signup_view(request: HttpRequest):
    if request.user.is_authenticated:
        return redirect('main:home_view')
    if request.method == 'POST':
        user_form = CustomUserCreationForm(request.POST)
        profile_form = ProfileForm(request.POST, request.FILES)
        if user_form.is_valid() and profile_form.is_valid():
            with transaction.atomic():
                new_user = user_form.save()
                profile = profile_form.save(commit=False)
                profile.user = new_user
                profile_form.save()
                send_welcome_email(new_user)
                messages.success(request, "You have been register")
            return redirect('accounts:login_view')
        else:
            messages.error(request, "something goes Wrong")
            return render(request, 'accounts/signup.html', {
                'user_form': user_form,
                'profile_form': profile_form
            })

    return render(request, 'accounts/signup.html')


def developer_signup_view(request: HttpRequest):
    if request.user.is_authenticated:
        return redirect('main:home_view')

    if request.method == 'POST':
        user_form = CustomUserCreationForm(request.POST)
        developer_form = DeveloperProfileForm(request.POST)

        if user_form.is_valid() and developer_form.is_valid():
            with transaction.atomic():
                new_user = user_form.save()
                developer_group = Group.objects.get(name='Developer')
                new_user.groups.add(developer_group)
                developer_profile = developer_form.save(commit=False)
                developer_profile.user = new_user
                developer_profile.save()
                messages.success(request, "Developer account created successfully.")
                return redirect('accounts:login_view')
        else:
            messages.error(request, "Something went wrong.")
            return render(request, 'accounts/developer_signup.html', {
                'user_form': user_form,
                'developer_form': developer_form,
            })
    else:
        user_form = CustomUserCreationForm()
        developer_form = DeveloperProfileForm()

    return render(request, 'accounts/developer_signup.html', {
        'user_form': user_form,
        'developer_form': developer_form,
    })


def login_view(request: HttpRequest):
    if request.user.is_authenticated:
        return redirect('main:home_view')
    if request.method == 'POST':
        user = authenticate(
            request,
            username=request.POST['username'],
            password=request.POST['password']
        )
        if user:
            login(request, user)
            if request.user.groups.filter(name='Developer').exists():
                messages.success(request, "Logged in successufly")
                return redirect('main:home_view')
            messages.success(request, "Logged in successufly")
            return redirect('main:home_view')
        else:
            messages.error(request, "Your Username or Password is wrong, try again")

    return render(request, 'accounts/login.html')


def logout_view(request: HttpRequest):
    logout(request)
    return redirect('main:home_view')


def is_developer(user):
    return user.groups.filter(name='Developer').exists()


@login_required
def developer_dashboard(request: HttpRequest):
    if not is_developer(request.user):
        return HttpResponseForbidden()

    games = request.user.games.order_by('-created_at')
    return render(request, 'accounts/developer_dashboard.html', {'games': games})


def profile_view(request: HttpRequest):
    profile, created = Profile.objects.get_or_create(user=request.user)
    return render(request, 'accounts/profile.html', {'profile': profile})


def developer_profile_view(request: HttpRequest, username):
    dev_user = get_object_or_404(User, username=username)
    dev_profile = get_object_or_404(DeveloperProfile, user=dev_user)

    try:
        player_profile = Profile.objects.get(user=dev_user)
    except Profile.DoesNotExist:
        player_profile = None

    published_games = dev_user.games.filter(is_active=True).prefetch_related('genre')

    follower_count = FollowDeveloper.objects.filter(developer=dev_profile).count()

    is_following = False
    if request.user.is_authenticated and request.user != dev_user:
        is_following = FollowDeveloper.objects.filter(
            user=request.user,
            developer=dev_profile
        ).exists()

    announcements = dev_profile.announcements.all()[:10]

    is_owner = request.user == dev_user

    # private owner-only data
    private_data = {}
    if is_owner:
        from analytics.models import DeveloperEarnings, GameAnalytics
        from games.models import Game

        unpublished_games = dev_user.games.filter(is_active=False)

        total_revenue = DeveloperEarnings.objects.filter(
            developer=dev_profile
        ).aggregate(total=Sum('revenue'))['total'] or 0

        game_ids = dev_user.games.values_list('id', flat=True)
        total_purchases = GameAnalytics.objects.filter(
            game_id__in=game_ids
        ).aggregate(total=Sum('purchases'))['total'] or 0

        private_data = {
            'unpublished_games': unpublished_games,
            'total_revenue': total_revenue,
            'total_purchases': total_purchases,
        }

    announcement_form = AnnouncementForm() if is_owner else None

    context = {
        'dev_user': dev_user,
        'dev_profile': dev_profile,
        'player_profile': player_profile,
        'published_games': published_games,
        'follower_count': follower_count,
        'is_following': is_following,
        'announcements': announcements,
        'is_owner': is_owner,
        'announcement_form': announcement_form,
        **private_data,
    }

    return render(request, 'accounts/developer_profile.html', context)


@login_required
def follow_toggle_view(request: HttpRequest, developer_id):
    if request.method != 'POST':
        return HttpResponseForbidden()

    dev_profile = get_object_or_404(DeveloperProfile, id=developer_id)

    if request.user == dev_profile.user:
        return HttpResponseForbidden()

    follow, created = FollowDeveloper.objects.get_or_create(
        user=request.user,
        developer=dev_profile
    )

    if not created:
        follow.delete()

    return redirect('accounts:developer_profile', username=dev_profile.user.username)


@login_required
def my_orders_view(request):
    if request.user.groups.filter(name='Developer').exists():
        messages.warning(request, 'You are not allowed')
        return redirect('main:home_view')

    orders = (
        Order.objects
        .filter(user=request.user)
        .prefetch_related('items__game', 'gamekey_set__game')
        .order_by('-created_at')
    )

    return render(request, 'accounts/my_orders.html', {
        'orders': orders,
    })


def send_welcome_email(user):
    if not user.email:
        return

    subject = 'Welcome to Gaming Platform'

    html_message = render_to_string('accounts/emails/welcome_email.html', {
        'user': user,
    })
    plain_message = strip_tags(html_message)

    send_mail(
        subject=subject,
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=html_message,
        fail_silently=False,
    )