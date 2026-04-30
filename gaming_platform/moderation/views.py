from django.shortcuts import render

# Create your views here.

def moderation_view(request):
    # Logic for the view
    return render(request, 'moderation/moderation.html')