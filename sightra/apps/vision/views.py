from django.shortcuts import render

# Create your views here.
def vision(request):
    return render(request, "vision.html")