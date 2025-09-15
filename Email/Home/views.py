from django.shortcuts import render, redirect
from CreateUser.models import emailUsers

def Home(request):
    user_count = emailUsers.objects.count()
    context = {'user_count': user_count}
    return render(request, 'Home/index.html', context)

def documentation(request):
    return render(request, 'Home/documentation.html')