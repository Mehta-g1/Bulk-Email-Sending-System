from django.shortcuts import render,redirect
from .models import emailUsers, Receipent
from django.shortcuts import HttpResponse
from django.contrib import messages
from .utils import send_bulk_email

def Login(request):
    return render(request, 'CreateUser/login.html' ,{'title':'Login Page'})

def verify(request) :
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get('password')
        print("---------\nEmail:",email)
        print("password:",password)
        print("----------")

        try:
            user = emailUsers.objects.get(email_address=email)

            if user.login_password == password:   
                messages.success(request, "Login Successful!")
                request.session["user_id"] = user.id
                request.session.set_expiry(0)
                return redirect("dashboard")  
            else:
                messages.error(request, "Invalid Password")
        except emailUsers.DoesNotExist:
            messages.error(request, "Email not registered")

    return render(request, 'CreateUser/login.html' ,{'title':'Login Page'})


def signUp(request):
    return render(request, 'CreateUser/signUp.html', {'title': "SignUp Page"})


def signingUp(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        login_password = request.POST.get('loginPassword')
        email_password = request.POST.get("emailPassword")

        print("---------------\nName:",name)
        print("Email:", email)
        print("login_password:", login_password)
        print("Email Password:", email_password)
        print("----------------\n\n")

        emailUsers.objects.create(
            name = name,
            email_address = email,
            email_password = email_password,
            login_password = login_password
        )
        messages.success(request,"SignUp successfully ! ✅")
        return redirect("/")
    return render(request, 'CreateUser/signUp.html', {'title':'SignUp Page'})



def dashboard(request):
    user_id = request.session.get("user_id")
    if not user_id:
        messages.warning(request, "Login first")
        return redirect('/')
    user = emailUsers.objects.get(id=user_id)

    recipients = Receipent.objects.filter(Sender__id=user_id)
    receipient_list = []
    for receipient in recipients:
        receipient_list.append( {'name':receipient.name,'email':receipient.email} )

    title = f"Welcome, {user.name}"
    # print(receipient_list)

    return render(request, 'CreateUser/dashboard.html',{'title':title, 'receipients':receipient_list})



def logout(request):
    request.session.flush()

    return redirect("/")


def sendMail(request):
    user_id = request.session.get("user_id")
    if not user_id:
        return redirect('/')
    send_bulk_email(user_id)
    messages.success(request, "Mail successfully sent")
    return redirect('dashboard')