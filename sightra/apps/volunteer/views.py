from django.shortcuts import render

# Create your views here.
def sightra_connect(request):
    return render(request, "sightra-connect.html")


def live_call(request):
    return render(request, "live-call.html")


