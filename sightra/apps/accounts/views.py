from django.shortcuts import render

# Create your views here.
def signin(request):
    return render(request, 'signin.html')

def signup(request):
    return render(request, 'signup.html')

# def profile(request):
#     return render(request, 'profile.html')

# def logout(request):
#     return render(request, 'logout.html')