from django.shortcuts import render, redirect
from .models import Template
from django.contrib import messages
from CreateUser.models import emailUsers
from datetime import datetime
from django.shortcuts import get_object_or_404


def Templates(request):
    user_id = request.session.get('user_id')
    if not user_id:
        messages.error(request, "Login First")
        return redirect('Login')
    templates = Template.objects.filter(user = emailUsers.objects.get(id=user_id))
    template_list = []
    for t in templates:
        if not t.primary:
            template_list.append({
                    'id':t.id,
                    'template_name' : t.template_name,
                    'subject' : t.subject, 
                    'created_at':t.created_at,
                    'updated_at':t.updated_at,
                })
        else:
            primary_template = {
                'id':t.id,
                'template_name' : t.template_name,
                'subject' : t.subject, 
                'created_at':t.created_at,
                'updated_at':t.updated_at,
            }

    name = emailUsers.objects.get(id=user_id).name
    return render(request, 'EmailTemplates/templates.html',{
        'templates':template_list,
        'primary_template':primary_template,
        'title':f"{name} -Template list",
        'username':name.split(' ')[0],
        'image':emailUsers.objects.get(id=user_id).image
    })
       

def MakePrimary(request, id):
    user_id = request.session.get('user_id')
    if not user_id:
        messages.error(request, "Login First")
        return redirect('Login')
    try:
        user = emailUsers.objects.get(id=user_id)
        templates  = Template.objects.filter(user = user)
        for t in templates:
            if t.id == id:
                t.primary = True
            else:
                t.primary = False
            t.save() 
        messages.success(request, "Primary template updated !")
    except Exception as e:
        messages.error(e)
        return redirect('dashboard')
    return redirect('templates')


def viewTemplate(request,id):
    user_id = request.session.get('user_id')
    if not user_id:
        messages.error(request, "Login First")
        return redirect('Login')
    try:
        template = Template.objects.get(id=id)
    except Exception as e:
        messages.error(request, "Template not found !")
        return redirect('templates')
    context = {
        'title':f'{template.template_name} -{template.user.name}',
        'id':template.id,
        'name':template.template_name,
        'subject':template.subject,
        'created_at':template.created_at,
        'updated_at':template.updated_at,
        'body':template.body,
        'username':template.user.name.split(' ')[0],
        'image':template.user.image
    }
    return render(request, 'EmailTemplates/view.html', context)


def editTemplate(request,id):
    user_id = request.session.get('user_id')
    if not user_id:
        messages.error(request, "Login First")
        return redirect('Login')
    try:
        template = Template.objects.get(id=id)
    except Exception as e:
        messages.error(request, "Template not found !")
        return redirect('templates')
    context = {
        'title':f'{template.template_name} -{template.user.name}',
        'id':template.id,
        'name':template.template_name,
        'subject':template.subject,
        'created_at':template.created_at,
        'updated_at':template.updated_at,
        'body':template.body,
        'username':template.user.name.split(' ')[0],
        'image':template.user.image
    }

    if request.method == "POST":
        name = request.POST.get('name')
        subject = request.POST.get('subject')
        body = request.POST.get('body')

        try:
            template = Template.objects.get(id=id)
            template.template_name = name
            template.subject = subject
            template.body = body
            template.updated_at = datetime.now()  # This stores the complete date & time (timezone-aware)
            template.save()
        except Exception as e:
            messages.error(request, f"Error: {e}")
            return redirect('templates')
        messages.success(request, "Mail template updated successfully !")
        return redirect('templates')
    return render(request, 'EmailTemplates/edit.html', context)



def deleteTemplate(request, id):
    user_id = request.session.get('user_id')
    if not user_id:
        messages.error(request, "Login First")
        return redirect('Login')
    
    template = get_object_or_404(Template, id=id)

    template.delete()
    messages.success(request, "Email template deleted successfully !")
    return redirect('templates')


def createTemplate(request):
    user_id = request.session.get('user_id')
    if not user_id:
        messages.error(request, "Login first")
        return redirect('Login')
    
    if request.method == "POST":
        name = request.POST.get('name')
        subject = request.POST.get('subject')
        body = request.POST.get('body')
        user = get_object_or_404(emailUsers, pk=user_id)
        primary = request.POST.get('primary')

        t = Template.objects.create(
            template_name = name,
            user = user,
            subject = subject,
            body = body,
        )
        if primary:
            templates = Template.objects.filter(user=user)
            for e in templates:
                if e.id == t.id:
                    e.primary = True
                else:
                    e.primary = False
                e.save() 
        messages.success(request, "Email template created successfully !")
        return redirect('templates')
    
    return render(request, 'EmailTemplates/create.html',{
        'title':'Create new Template',
        'username':get_object_or_404(emailUsers, pk=user_id).name.split(' ')[0],
        'image':get_object_or_404(emailUsers, pk=user_id).image
    })