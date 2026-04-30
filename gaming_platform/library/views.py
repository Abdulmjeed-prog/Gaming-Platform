from django.shortcuts import render

# Create your views here.

def library_view(request):
    # Logic for the view
    return render(request, 'library/library.html')