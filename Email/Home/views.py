from django.shortcuts import render, redirect
from CreateUser.models import emailUsers
from .models import Contact
from django.contrib import messages
from CreateUser.models import Receipent

# Home page view
def Home(request):
    user_count = emailUsers.objects.count()

    receipient_count = len(Receipent.objects.all())
    context = {'user_count': user_count,'r_count':receipient_count}
    return render(request, 'Home/index.html', context)

# Documentation page view
def documentation(request):
    return render(request, 'Home/documentation.html')

# Contact Us page view
def contact_us(request):
    if request.method == 'POST':
        user_type = request.POST.get('user_type')
        email = request.POST.get('email')
        query = request.POST.get('query')
        suggestion = request.POST.get('suggestion')

        contact = Contact(
            user_type=user_type,
            email=email,
            query=query,
            suggestion=suggestion
        )
        contact.save()
        messages.success(request, 'Your message has been sent successfully!')
        return redirect('contact_us')
    return render(request, 'Home/contact.html')

# About Us page view
def about_us(request):
    return render(request, 'Home/about.html')