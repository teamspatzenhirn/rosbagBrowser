from django.shortcuts import render


def index(request):
    return render(request, "landingpage/index.html")


def login(request):
    return render(request, "landingpage/login.html")
