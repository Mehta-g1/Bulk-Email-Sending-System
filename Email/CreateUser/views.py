from django.shortcuts import render,redirect
from .models import emailUsers, Receipent
from django.shortcuts import HttpResponse, get_object_or_404
from django.contrib import messages
from .utils import send_bulk_email

def Login(request):
    if 'user_id' in request.session:
        del request.session['user_id'] 
    return render(request, 'CreateUser/login.html' ,{'title':'Login Page'})

def Authenticate(request) :
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
        post = request.POST.get('post')
        department = request.POST.get('department')
        about_you = request.POST.get('about_you')
        personalEmail = request.POST.get('personalEmail')
        dob = request.POST.get('dob')
        fatherName = request.POST.get('fatherName')
        address = request.POST.get('address')

        emailUsers.objects.create(
            name=name,
            email_address=email,
            email_password=email_password,
            login_password=login_password,
            post=post,
            department=department,
            about_you=about_you,
            personalEmail=personalEmail,
            dob=dob,
            fatherName=fatherName,
            address=address
        )
        messages.success(request, "SignUp successfully ! ✅")
        return redirect("/")
    return render(request, 'CreateUser/signUp.html', {'title': 'SignUp Page'})



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

def profile(request):
    user_id = request.session.get("user_id")

    user = get_object_or_404(emailUsers, pk=user_id)
    if user:

        data = {
            'title': user.name,
            'name':user.name,
            'email':user.email_address,
            'emailPassword':user.email_password,
            'loginPassword':user.login_password,
            'f_name':user.fatherName,
            'dob':user.dob,
            'about':user.about_you,
            'post':user.post,
            'personalEmail':user.personalEmail,
            'address':user.address,
            'department':user.department
        }
        
        return render(request, "CreateUser/viewProfile.html", context=data)
    messages.error(request, "Something went wrong !")
    return redirect('dashboard')


def logout(request):
    if 'user_id' in request.session:
        del request.session['user_id'] 
    messages.success(request, "Logged out successfully !")
    return redirect("/")


def sendMail(request):
    user_id = request.session.get("user_id")
    if not user_id:
        return redirect('/')
    send_bulk_email(user_id)
    messages.success(request, "Mail successfully sent")
    return redirect('dashboard')


