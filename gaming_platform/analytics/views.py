from django.shortcuts import render

# Create your views here.


def analytics_view(request):
    # Logic for the view
    return render(request, 'analytics/analytics.html')