from django.shortcuts import render

# Create your views here.

def social_view(request):
    # Logic for the view
    return render(request, 'social/social.html')