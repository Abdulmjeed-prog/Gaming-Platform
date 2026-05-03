from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages


def developer_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login_view')
        if not request.user.groups.filter(name='Developer').exists():
            messages.error(request, 'A developer account is required.')
            return redirect('main:home_view')
        return view_func(request, *args, **kwargs)
    return wrapper