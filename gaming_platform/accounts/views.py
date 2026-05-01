from django.shortcuts import render, redirect
from django.http import HttpRequest, HttpResponse
from django.contrib.auth.models import Group, User
from django.contrib.auth import authenticate, login,logout
from django.contrib import messages
from django.contrib.auth.forms import UserCreationForm
from django.db import transaction
from .forms import ProfileForm, CustomUserCreationForm , CustomUserUpdateForm, DeveloperProfileForm
from django.contrib.auth.decorators import login_required


# Create your views here.

def signup_view(request:HttpRequest):
    if request.user.is_authenticated:
        return redirect('main:home_view')
    if request.method == 'POST':
        user_form = CustomUserCreationForm(request.POST)
        profile_form = ProfileForm(request.POST,request.FILES)
        if user_form.is_valid() and profile_form.is_valid():
            with transaction.atomic():
                new_user = user_form.save()
                profile = profile_form.save(commit=False)
                profile.user = new_user
                profile_form.save()
                messages.success(request, "You have been register")
            return redirect('accounts:login_view')
        else:
            print(user_form.errors)
            messages.error(request, "something goes Wrong")
            return render(request, 'accounts/signup.html', {'user_form': user_form,'profile_form': profile_form})
        
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


def login_view(request:HttpRequest):
    if request.user.is_authenticated:
        return redirect('main:home_view')
    if request.method == 'POST':
        user = authenticate(request, username = request.POST['username'], password = request.POST['password'])
        if user:
            login(request,user)
            if request.user.groups.filter(name='Developer'):
                messages.success(request, "Logged in successufly")
                return redirect('games:all_games')
            messages.success(request, "Logged in successufly")
            return redirect('main:home_view')
        else:
            messages.error(request, "Your Username or Password is wrong, try again")
            
    
    return render(request, 'accounts/login.html')

def logout_view(request:HttpRequest):
    logout(request)
    #response = redirect(request.GET.get("next"))
    return redirect('main:home_view')



def is_developer(user):
    return user.groups.filter(name='developer').exists()
 
 
@login_required
def developer_dashboard(request: HttpRequest):
    if not is_developer(request.user):
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden()
 
    games = request.user.games.order_by('-created_at')
    return render(request, 'accounts/developer_dashboard.html', {'games': games})

