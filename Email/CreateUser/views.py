from django.shortcuts import render,redirect
from .models import emailUsers, Receipent, reset_link
from django.shortcuts import HttpResponse, get_object_or_404
from django.contrib import messages
from .utils import send_bulk_email, check_token, send_forget_password_link
from django.utils.crypto import get_random_string
# Login view
def Login(request):
    if 'user_id' in request.session:
        del request.session['user_id'] 
        messages.info(request, "Previous session has been cleared.")
    return render(request, 'CreateUser/login.html' ,{'title':'Login Page'})

# Verify Login
def Authenticate(request) :
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get('password')

        try:
            user = emailUsers.objects.get(email_address=email)

            if user.login_password == password:   
                messages.success(request, "Login Successful!")
                request.session["user_id"] = user.id
                request.session.set_expiry(0)
                return redirect("dashboard")  
            else:
                messages.warning(request, "Incorrect password. Please try again.")
        except emailUsers.DoesNotExist:
            messages.warning(request, "This email is not registered. Please sign up first.")

    return render(request, 'CreateUser/login.html' ,{'title':'Login Page'})

# SignUp page
def signUp(request):
    return render(request, 'CreateUser/signUp.html', {'title': "SignUp Page"})

# Verify and signing Up 
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
        messages.success(request, "Sign up completed successfully!")
        return redirect("/")
    return render(request, 'CreateUser/signUp.html', {'title': 'SignUp Page'})

# View user dashboard
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

    return render(request, 'CreateUser/dashboard.html',{'title':title, 'receipients':receipient_list})

# Views user profile
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
            'department':user.department,
            'image':user.image
        }
        
        return render(request, "CreateUser/viewProfile.html", context=data)
    
    messages.error(request, "An error occurred while retrieving the profile.")
    return redirect('dashboard')

# Edit user profile page
def edit_profile(request):
    user_id = request.session.get("user_id")
    if not user_id:
        messages.warning(request, "Please log in to edit your profile.")
        return redirect('profile')
    user = get_object_or_404(emailUsers, pk=user_id)
    return render(request, 'CreateUser/editProfile.html', {'user': user})  

# Actual editing user data  
def edit_profile_process(request):
    user_id = request.session.get("user_id")
    if not user_id:
        messages.warning(request, "Please log in to edit your profile.")
        return redirect('profile')
    user = get_object_or_404(emailUsers, pk=user_id)

    if request.method == 'POST':
        user.name = request.POST.get('name')
        user.personalEmail = request.POST.get('personalEmail')
        user.post = request.POST.get('post')
        user.department = request.POST.get('department')
        user.about_you = request.POST.get('about_you')
        user.fatherName = request.POST.get('fatherName')
        user.address = request.POST.get('address')
        user.save()
        messages.success(request, "Your profile has been updated.")
        return redirect('profile')

    messages.error('Something went wrong !')
    return redirect('profile')    
    
# change password page
def change_password(request):
    user_id = request.session.get("user_id")
    if not user_id:
        messages.warning(request, "Login first")
        return redirect('/')
    
    if request.method == 'POST':
        user = get_object_or_404(emailUsers, pk=user_id)
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')

        if user.login_password == current_password:
            user.login_password = new_password
            user.save()
            messages.success(request, "Your password has been updated successfully.")
            return redirect('profile')
        else:
            messages.warning(request, "The current password you entered is incorrect.")
    
    return render(request, 'Createuser/changePassword.html',{'name':get_object_or_404(emailUsers, pk=user_id).name})

# forget password page
def forgot_password(request):
    if request.method == "POST":
        email = request.POST.get('email')
        
        user = get_object_or_404(emailUsers,email_address = email )
        if user:
            token = get_random_string(32)
            
            reset_link.objects.create(
                user = user,
                token = token
            )
            
            send_forget_password_link(email, token)
            messages.success(request, "Reset link sent to registered email")
            return redirect('Login')
        else:
            messages(request, "Something went wrong !, May be user does not exists !")
    return render(request, 'CreateUser/forgot_password.html')

def reset_password(request, token):

    if request.method == "POST":
        Token = get_object_or_404(reset_link, token=token)
        user = Token.user
        new_password = request.POST.get('password')
        user.login_password = new_password
        Token.is_attempted = True
        
        Token.save()
        user.save()
        messages.success(request,"Password changed successfully !")
        return redirect("Login")
    
    if check_token(token):
        return render(request, 'CreateUser/resetPassword.html',{'token':token})

    return render(request, 'CreateUser/expirePage.html')

            

    return  redirect('Login')

    
# logout views
def logout(request):
    if 'user_id' in request.session:
        del request.session['user_id'] 
    messages.success(request, "Logged out successfully !")
    return redirect("Login")

# send mail view (Only for testing )

def sendMail(request):
    user_id = request.session.get("user_id")
    if not user_id:
        return redirect('/')
    send_bulk_email(user_id)
    messages.success(request, "Mail successfully sent")
    return redirect('dashboard')
