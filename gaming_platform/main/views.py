from django.shortcuts import render, redirect
from django.http import HttpRequest, HttpResponse

# Create your views here.

def home_view(request:HttpRequest):
    if request.user.groups.filter(name='Developer'):
        print('yes im')
    return render(request, 'main/home.html')