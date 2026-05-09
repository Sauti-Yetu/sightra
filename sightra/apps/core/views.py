from django.shortcuts import render

def index(request):
    return render(request, "index.html")

def landing_page(request):
    return render(request, "landing-page.html")

