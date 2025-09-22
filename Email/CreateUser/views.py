from django.shortcuts import render,redirect
from .models import emailUsers, Receipent, reset_link
from django.shortcuts import HttpResponse, get_object_or_404
from django.contrib import messages
from .utils import send_bulk_email, check_token, send_forget_password_link,profileCompletetion
from django.utils.crypto import get_random_string
from django.db.models import Q
from django.utils.timezone import now
from EmailTemplates.models import Template
import os
# Login view
def Login(request):
    if 'user_id' in request.session:
        del request.session['user_id'] 
        messages.info(request, "Previous session has been cleared.")
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
    return render(request, 'CreateUser/login.html' ,{'title':'Login Page'})


# SignUp page
def signUp(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        login_password = request.POST.get('password')
        mobile = request.POST.get('phone')

        if emailUsers.objects.filter(email_address=email).exists():
            messages.warning(request, "Email is already registered. Please use a different email.")
            return render(request, 'CreateUser/signUp.html', {'title': "SignUp Page"})
        
        user = emailUsers.objects.create(
            name=name,
            email_address=email,
            login_password=login_password,
            phone=mobile,
        )
        
        Template.objects.create(
            template_name = "Default template",
            user = user,
            subject = "This if default mail template",
            body = "Welcome to Bulk Email sending system",
            primary = True,
        )
        messages.success(request, "Sign up completed successfully!")
        messages.info(request, "You can now log in with your credentials.")
        return redirect("Login")
    return render(request, 'CreateUser/signUp.html', {'title': "SignUp Page"})

# View user dashboard
def dashboard(request):
    user_id = request.session.get("user_id")
    if not user_id:
        messages.warning(request, "Login first")
        return redirect('Login')
    
    user = emailUsers.objects.get(id=user_id)
    # if not user.email_password:
    #     messages.warning(request, "Please update your email settings in profile before proceeding.")
    #     return redirect('edit_profile')

    recipients = Receipent.objects.filter(Sender__id=user_id)
    search_query = ""
    if request.method == "POST":
        search_query = request.POST.get("search", "").strip()
        if search_query:
            recipients = recipients.filter(
                Q(name__icontains=search_query) |
                Q(email__icontains=search_query) |
                Q(receipent_category__icontains=search_query) |
                Q(comment__icontains=search_query)
            )

    receipient_list = [
        {
            'id':r.id,
            'name': r.name,
            'email': r.email,
            'category': r.receipent_category,
            'comment': r.comment,
            'added_date': r.added_date,
        }
        for r in recipients
    ]

    title = f"Welcome, {user.name}"
    
    return render(
        request,
        'CreateUser/dashboard.html',
        {
            'image': user.image,
            'progress': profileCompletetion(user),
            'title': title,
            'receipients': receipient_list,
            'username': str(user.name).split(" ")[0],
            'search_query': search_query,
        }
    )

# Views user profile
def profile(request):
    user_id = request.session.get("user_id")
    if not user_id:
        messages.warning(request, "Please log in to view your profile.")
        return redirect('Login')

    user = get_object_or_404(emailUsers, pk=user_id)

    # Profile completion logic

    progress = profileCompletetion(user)

    # Recent templates
    recent_templates = Template.objects.filter(user=user).order_by('-created_at')[:5]

    # Recent recipients
    recent_recipients = Receipent.objects.filter(Sender=user).order_by('-added_date')[:5]

    # Static data for attachments
    recent_attachments = [
        {'name': 'report-final.pdf', 'size': '1.2 MB', 'date': '2023-10-26'},
        {'name': 'project-plan.docx', 'size': '450 KB', 'date': '2023-10-25'},
        {'name': 'invoice-q3.xlsx', 'size': '78 KB', 'date': '2023-10-24'},
    ]

    data = {
        'user': user,
        'progress': progress,
        'image': user.image,
        'recent_templates': recent_templates,
        'recent_recipients': recent_recipients,
        'recent_attachments': recent_attachments,
        'username': str(user.name).split(" ")[0],
        'title': f"{user.name}'s Profile",
    }
    
    return render(request, "CreateUser/viewProfile.html", context=data)


# Edit user profile page
def edit_profile(request):
    user_id = request.session.get("user_id")
    if not user_id:
        messages.warning(request, "Please log in to edit your profile.")
        return redirect('profile')
    user = get_object_or_404(emailUsers, pk=user_id)
    progress = profileCompletetion(user)
    image = user.image

    return render(request, 'CreateUser/editProfile.html',  {
                'image':user.image,
                'username':str(user.name).split(" ")[0],
                'user': user, 
                'title':f'Edit Profile -{user.name}', 
                'progress': progress, 
                'image': image
            })

# Actual editing user data  
def edit_profile_process(request):
    user_id = request.session.get("user_id")
    if not user_id:
        messages.warning(request, "Please log in to edit your profile.")
        return redirect('profile')
    
    user = get_object_or_404(emailUsers, pk=user_id)

    if request.method == 'POST':
        user.name = request.POST.get('name', user.name)
        user.personalEmail = request.POST.get('personalEmail', user.personalEmail)
        user.phone = request.POST.get('phone', user.phone)
        user.dob = request.POST.get('dob', user.dob)
        user.org_name = request.POST.get('org_name', user.org_name)
        user.post = request.POST.get('post', user.post)
        user.department = request.POST.get('department', user.department)
        user.address = request.POST.get('address', user.address)
        user.about_you = request.POST.get('about_you', user.about_you)

        if 'image' in request.FILES:
            old_image = user.image
            user.image = request.FILES['image']
            if old_image and old_image.path != user.image.path:
                if os.path.isfile(old_image.path):
                    os.remove(old_image.path)
                    # print("Old image file deleted:", old_image.path)

        user.save()
        messages.success(request, "Your profile has been updated successfully.")
        return redirect('dashboard')

    messages.warning(request, 'Invalid request method.')
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
        
        Token.new_password = new_password
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

def viewReceipent(request, receipient_id):
    user_id = request.session.get("user_id")
    if not user_id:
        messages.warning(request, "Login first")
        return redirect('Login')

    receipient = get_object_or_404(Receipent, id=receipient_id, Sender__id=user_id)
    title = f"{receipient.name} -{emailUsers.objects.get(id=user_id).name}"
    return render(request, "Receipent/view.html", {
        "receipient": receipient,
        'title':title
    })


def editReceipent(request, receipient_id):
    user_id = request.session.get("user_id")
    if not user_id:
        messages.warning(request, "Login first")
        return redirect("Login")  
    user = get_object_or_404(emailUsers, pk=user_id)

    receipent = get_object_or_404(Receipent, Sender=user, pk=receipient_id)

    if request.method == "POST":
        receipent.name = request.POST.get('name')
        receipent.email = request.POST.get('email')
        receipent.receipent_category = request.POST.get('category')
        receipent.comment = request.POST.get('comment')
        receipent.added_date = now()

        receipent.save()
        messages.success(request, "Receipient details update successfully !")
        return redirect('dashboard')
        

    return render(request, "Receipent/edit.html", {
        "receipient": receipent
    })



    # Delete Recipient

def deleteRecipient(request, receipient_id):
    user_id = request.session.get("user_id")
    if not user_id:
        messages.warning(request, "Login first")
        return redirect("Login")  

    # get logged in user
    user = get_object_or_404(emailUsers, id=user_id)

    # get recipient only if it belongs to this user
    recipient = get_object_or_404(Receipent, id=receipient_id, Sender=user)

    # delete
    recipient.delete()
    messages.success(request, "Recipient deleted successfully.")
    return redirect("dashboard")

 # Add new receipent

def addReceipent(request):
    user_id = request.session.get('user_id')
    if not user_id:
        messages.warning(request, "Login first")
        return redirect('Login')
    
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        category = request.POST.get('category')
        comment = request.POST.get('comment')

        user = get_object_or_404(emailUsers, pk=user_id)
        Receipent.objects.create(
            Sender = user,
            email = email,
            name = name,
            receipent_category = category,
            comment = comment,
        )
        messages.success(request, "Receipient added successfuly !")
        return redirect('dashboard')
    return render(request, 'Receipent/add.html',{'title':'Add Recipient'})


# send mail view 
def sendMail(request):
    user_id = request.session.get('user_id')
    if not user_id:
        messages.warning(request, 'Login First')
        return redirect('Login')
    user = get_object_or_404(emailUsers, pk=user_id)
    if not user.email_password:
        messages.warning(request, "Please update your email settings in profile before proceeding.")
        return redirect('edit_profile')

     # Process the form submission
    if request.method == "POST":
        selected_ids = request.POST.getlist("selected") 
        
        if not selected_ids:
            messages.warning(request, "No recipients selected!")
            return redirect("dashboard")

        send_bulk_email(user_id, selected_ids)

        # for r in Receipent.objects.filter(id__in=selected_ids):
        #     messages.success(request,f"Sending mail to: {r.email}") 

        messages.success(request, f"Emails sent to {len(selected_ids)} recipient(s)!")
        return redirect("dashboard")
    else:
        return redirect("dashboard")

def account_settings(request):
    user_id = request.session.get("user_id")
    if not user_id:
        messages.warning(request, "Please log in to access account settings.")
        return redirect('Login')

    user = get_object_or_404(emailUsers, pk=user_id)

    if request.method == 'POST':
        user.email_password = request.POST.get('email_password', user.email_password)
        user.email_host = request.POST.get('email_host', user.email_host)
        user.email_port = request.POST.get('email_port', user.email_port)
        user.use_tls = 'use_tls' in request.POST
        
        user.save()
        messages.success(request, "Your account settings have been updated.")
        return redirect('profile')
    progress = profileCompletetion(user)
    username = str(user.name).split(" ")[0]
    image = user.image
    return render(request, 'CreateUser/accountSettings.html', 
            {
                'user': user,
                'title': 'Account Settings',
                'progress': progress,
                'image': image,
                'username': username,
                'title': f'Account Settings -{username}',
            })