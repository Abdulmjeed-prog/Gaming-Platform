from django.shortcuts import render

# Create your views here.

def commerce_view(request):
    # Logic for the view
    return render(request, 'commerce/commerce.html')