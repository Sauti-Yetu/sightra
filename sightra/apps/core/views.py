from django.shortcuts import render

def dashboard(request):
    return render(request, "dashboard.html")

def landing_page(request):
    return render(request, "landing-page.html")

