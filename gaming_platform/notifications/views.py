from django.shortcuts import render

# Create your views here.

def notifications_view(request):
    # Logic for the view
    return render(request, 'notifications/notifications.html')