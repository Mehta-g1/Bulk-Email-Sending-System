from django.shortcuts import render,redirect
from .models import emailUsers, Receipent, reset_link, UserFiles, Receipent_Group
from django.shortcuts import HttpResponse, get_object_or_404
from django.contrib import messages
from .utils import send_bulk_email, check_token, send_forget_password_link,profileCompletetion, extract_receipients_from_file
from django.utils.crypto import get_random_string
from django.db.models import Q
from django.utils.timezone import now
from EmailTemplates.models import Template
import os
import logging

# Configure logger
logger = logging.getLogger(__name__)


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

    recipients = Receipent.objects.filter(Sender__id=user_id).order_by('-added_date')
    search_query = ""
    selected_group_id = ""

    if request.method == "POST":
        search_query = request.POST.get("search", "").strip()
        selected_group_id = request.POST.get("group_filter", "")

        if selected_group_id and selected_group_id != 'all':
            recipients = recipients.filter(group__id=selected_group_id)
        
        if search_query:
            recipients = recipients.filter(
                Q(name__icontains=search_query) |
                Q(email__icontains=search_query) |
                Q(receipent_category__icontains=search_query) |
                Q(comment__icontains=search_query) |
                Q(source__icontains=search_query) |
                Q(group__group__icontains=search_query)
            ).order_by('-added_date')

    user_groups = Receipent_Group.objects.filter(user=user)
    receipient_list = [
        {
            'id':r.id,
            'name': r.name,
            'email': r.email,
            'category': r.receipent_category,
            'comment': r.comment,
            'added_date': r.added_date,
            'source': r.source,
            'group': r.group,
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
            'user_groups': user_groups,
            'selected_group_id': int(selected_group_id) if selected_group_id and selected_group_id != 'all' else None,
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

    recent_templates = Template.objects.filter(user=user).order_by('-created_at')[:5]

    recent_recipients = Receipent.objects.filter(Sender=user).order_by('-added_date')[:5]
    recent_attachments = UserFiles.objects.filter(user=user).order_by('-uploaded_at')[:5]
    total_sent_mail = sum(r.send_time for r in Receipent.objects.filter(Sender=user))
    groups = Receipent_Group.objects.filter(user=user).count()
    user_groups = Receipent_Group.objects.filter(user=user).order_by('-created_at')


    data = {
        'user': user,
        'progress': progress,
        'image': user.image,
        'recent_templates': recent_templates,
        'recent_recipients': recent_recipients,
        'recent_attachments': recent_attachments,
        'username': str(user.name).split(" ")[0],
        'title': f"{user.name}'s Profile",
        'total_sent_mail': total_sent_mail,
        'groups': groups,
        'user_groups': user_groups,
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
                    logger.info(f"Old image file deleted: {old_image.path}")

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
            
            send_forget_password_link(request, email, token)
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
    progress = profileCompletetion(emailUsers.objects.get(id=user_id))
    image = emailUsers.objects.get(id=user_id).image
    return render(request, "Receipent/view.html", {
        "receipient": receipient,
        'title':title,
        'progress': progress,
        'image': image,
        'username': str(emailUsers.objects.get(id=user_id).name).split(" ")[0],
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
    
    progress = profileCompletetion(user)
    image = user.image
    username = str(user.name).split(" ")[0]

    return render(request, "Receipent/edit.html", {
        "receipient": receipent,
        'progress': progress,
        'image': image,
        'username': username,
        'title': f'Edit Recipient - {receipent.name}',
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
        group_input = request.POST.get('group')
        new_group_name = request.POST.get('new_group_name')

        user = get_object_or_404(emailUsers, pk=user_id)

        # Logic to handle new group creation
        if new_group_name:
            # Create new group
            group = Receipent_Group.objects.create(group=new_group_name, user=user)
        elif not group_input or group_input == '0':
            messages.warning(request, "Please select a group or create a new one")
            return redirect('add_recepient')
        else:
            group = Receipent_Group.objects.get(pk=group_input, user=user)

        Receipent.objects.create(
            Sender = user,
            email = email,
            name = name,
            group = group,
            receipent_category = category,
            comment = comment,
        )
        messages.success(request, "Receipient added successfuly !")
        return redirect('dashboard')
    user = get_object_or_404(emailUsers, pk=user_id)
    username = user.name
    image = user.image
    progress = profileCompletetion(user)
    groups = Receipent_Group.objects.filter(user=user)
    return render(
            request, 
            'Receipent/add.html',
            {
                'image': image,
                'username': username,
                'progress': progress,
                'title':'Add Recipient',
                'groups':groups,
                
            }
        )

def submit_form(request):
    user_id = request.session.get('user_id')
    if not user_id:
        messages.warning(request, 'Login First')
        return redirect('Login')    
    if request.method == "POST":
        action = request.POST.get('action')

        if action == 'send':
            sendMail(request)
        elif action == 'delete':
            delete_selected_recipients(request)
        else:
            messages.warning(request, "Something went wrong !")
            return redirect("dashboard")
    return redirect("dashboard")


def add_in_bulk(request):
    user_id = request.session.get('user_id')
    if not user_id:
        messages.warning(request,"Login first ")
        return redirect('Login')
    
    user = get_object_or_404(emailUsers, pk=user_id)
    image = user.image
    username = str(user.name).split(" ")[0]
    
    if request.method == "POST":
        file = request.FILES.get('bulk_file') 
        filename = file.name.lower()
        group_input = request.POST.get('group')
        new_group_name = request.POST.get('new_group_name')

        if new_group_name:
            group = Receipent_Group.objects.create(group=new_group_name, user=user)
        elif not group_input or group_input == '0':
            messages.warning(request, "Please select a group or create a new one")
            return redirect('add_in_bulk')
        else:
            group = Receipent_Group.objects.get(pk=group_input, user=user)
        
        logger.info(f"Group Selection: {group_input}, New Group: {new_group_name}")

        if not file:
            logger.warning("No file uploaded!")
            messages.warning(request, "No file uploaded!")
            return redirect('add_in_bulk')
        if not (filename.endswith('.csv') or filename.endswith('.xls') or filename.endswith('.xlsx')):
            logger.warning("Invalid file type uploaded")
            messages.warning(request, "Please upload a valid CSV/XLS/XLSX file only.")
            return redirect('add_in_bulk')
        
        file_name = request.POST.get('file_name')
        file_type = ''
        if request.POST.get('file_type') == 'csv':
            file_type = 'CSV'
        elif request.POST.get('file_type') == 'xls':
            file_type = 'XLS'

        file_size = file.size
        logger.info(f"File name: {file_name}, Size: {file_size} bytes, Type: {file_type}")
        
        user_file = UserFiles.objects.create(
            user = user,
            file_name = file_name,
            file_size = f"{round(file_size/1024,2)} KB" if file_size < 1048576 else f"{round(file_size/(1024*1024),2)} MB",
            file_type = file_type,
            file = file,
        )
        if not extract_receipients_from_file(user, user_file,group, request):
            messages.warning(request, "There was an error processing the file. Please ensure it has the correct format.")
            return redirect('add_in_bulk')
       

        messages.success(request, "File uploaded successfully!")
        return redirect('dashboard')
    groups = Receipent_Group.objects.filter(user=user)
    return render(request, 'Receipent/add_in_bulk.html', 
                {
                    'title': 'Add Recipients in Bulk',
                    'image': image,
                    'username': username,
                    'progress': profileCompletetion(user),
                    'groups':groups,
                })

def delete_file(request, file_id):
    user_id = request.session.get('user_id')
    if not user_id:
        messages.warning(request, "Login first")
        return redirect('Login')

    user = get_object_or_404(emailUsers, pk=user_id)
    user_file = get_object_or_404(UserFiles, id=file_id, user=user)

    # Delete the file from storage
    if user_file.file and os.path.isfile(user_file.file.path):
        os.remove(user_file.file.path)
        logger.info(f"File deleted from storage: {user_file.file.path}")

    # Delete the database record
    user_file.delete()
    messages.success(request, "File deleted successfully.")
    return redirect('profile')

def delete_selected_recipients(request):
    user_id = request.session.get("user_id")
    if not user_id:
        messages.warning(request, "Login first")
        return redirect("Login")

    if request.method == 'POST':
        selected_ids = request.POST.getlist("selected")
        if not selected_ids:
            messages.warning(request, "No recipients selected to delete.")
            return redirect("dashboard")

        user = get_object_or_404(emailUsers, id=user_id)
        recipients_to_delete = Receipent.objects.filter(id__in=selected_ids, Sender=user)
        
        deleted_count = recipients_to_delete.count()
        recipients_to_delete.delete()
        
        messages.success(request, f"{deleted_count} recipient(s) deleted successfully.")
        return redirect("dashboard")
    else:
        return redirect("dashboard")

def read_file(request, file_id):
    user_id = request.session.get('user_id')
    if not user_id:
        messages.warning(request, "Login First")
        return redirect('Login')
    user = get_object_or_404(emailUsers, pk=user_id)
    user_file = get_object_or_404(UserFiles, id=file_id, user=user)
    if not user_file:
        messages.warning(request, "File not found.")
        return redirect('profile')
    if not user_file.file:
        messages.warning(request, "No file associated with this record.")
        return redirect('profile')
    try:
        file_path = user_file.file.path
        if not os.path.isfile(file_path):
            messages.warning(request, "File does not exist on the server. Upload again.")
            return redirect('dashboard')
        
        receipients = extract_receipients_from_file(user, user_file, request)
        if receipients:
            messages.success(request, f"Extracted {len(receipients)} recipients from the file.")
        else:
            messages.warning(request, "No recipients found in the file or there was an error processing it.")
        return redirect('dashboard')
    except Exception as e:
        logger.error(f"Error reading file: {e}")
        messages.warning(request, "An error occurred while reading the file.")
        return redirect('profile')
    
def sendMail(request):
    user_id = request.session.get('user_id')
    if not user_id:
        messages.warning(request, 'Login First')
        return redirect('Login')
    user = get_object_or_404(emailUsers, pk=user_id)
    if not user.email_password:
        messages.warning(request, "Please update your email settings in profile before proceeding.")
        return redirect('edit_profile')

    if request.method == "POST":
        selected_ids = request.POST.getlist("selected") 
        
        if not selected_ids:
            messages.warning(request, "No recipients selected!")
            return redirect("dashboard")

        if send_bulk_email(user_id, selected_ids):

        # for r in Receipent.objects.filter(id__in=selected_ids):
        #     messages.success(request,f"Sending mail to: {r.email}") 

            messages.success(request, f"Emails sent to {len(selected_ids)} recipient(s)!")
        else:
            messages.warning(request, "Something went wrong !")
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
    groups = Receipent_Group.objects.filter(user=user).count()
    total_sent_mail = sum(r.send_time for r in Receipent.objects.filter(Sender=user))
    return render(request, 'CreateUser/accountSettings.html', 
            {
                'user': user,
                'title': 'Account Settings',
                'progress': progress,
                'image': image,
                'username': username,
                'title': f'Account Settings -{username}',
                'total_sent_mail':total_sent_mail,
                'groups':groups,
            })


def create_group(request):
    user_id = request.session.get("user_id")
    if not user_id:
        messages.warning(request, "Login first")
        return redirect("Login")
    
    user = get_object_or_404(emailUsers, pk=user_id)

    if request.method == "POST":
        group_name = request.POST.get("group_name")
        if group_name:
            Receipent_Group.objects.create(user=user, group=group_name)
            messages.success(request, f"Group '{group_name}' created successfully!")
            return redirect("profile")
        else:
            messages.warning(request, "Group name cannot be empty.")
    
    return render(request, "CreateUser/group_form.html", {
        "title": "Create New Group",
        "user": user, 
        "username": str(user.name).split(" ")[0],
        'image': user.image
    })

def edit_group(request, group_id):
    user_id = request.session.get("user_id")
    if not user_id:
        messages.warning(request, "Login first")
        return redirect("Login")
    
    user = get_object_or_404(emailUsers, pk=user_id)
    group = get_object_or_404(Receipent_Group, pk=group_id, user=user)

    if request.method == "POST":
        group_name = request.POST.get("group_name")
        if group_name:
            group.group = group_name
            group.save()
            messages.success(request, "Group updated successfully!")
            return redirect("profile")
        else:
            messages.warning(request, "Group name cannot be empty.")
            
    return render(request, "CreateUser/group_form.html", {
        "title": "Edit Group",
        "group": group,
        "user": user,
        "username": str(user.name).split(" ")[0],
        'image': user.image
    })

def delete_group(request, group_id):
    user_id = request.session.get("user_id")
    if not user_id:
        messages.warning(request, "Login first")
        return redirect("Login")
    
    user = get_object_or_404(emailUsers, pk=user_id)
    group = get_object_or_404(Receipent_Group, pk=group_id, user=user)
    
    group_name = group.group
    group.delete()
    messages.success(request, f"Group '{group_name}' and its recipients deleted successfully.")
    return redirect("profile")