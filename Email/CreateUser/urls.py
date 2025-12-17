from django.urls import path, include
from . import views


urlpatterns = [
    path('login/',views.Login, name='Login'),
    path('signUp/',views.signUp, name='signUp'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('logout/',views.logout, name='logout'),
    path('viewProfile/', views.profile, name='profile'),
    path('edit-profile/', views.edit_profile, name='edit_profile'),
    path('edit-profile/process/', views.edit_profile_process, name='edit_profile_process'),
    path('change-password/', views.change_password, name='change_password'),
    path('account-settings/', views.account_settings, name='account_settings'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('reset-password/<str:token>/', views.reset_password, name='reset_password'),

    # Dashboard actions
    path('submit-form/', views.submit_form, name='submit_form'),
    # Receipient Management 
    path('receipient/add/', views.addReceipent, name="add_recepient"),
    path('receipient/bulk-add/', views.add_in_bulk, name="add_in_bulk"),
    path('file/delete/<int:file_id>/', views.delete_file, name='delete_file'),
    path('file/read/<int:file_id>/', views.read_file, name='read_file'),
    path('receipient/<int:receipient_id>/', views.viewReceipent, name="view_recepient"),
    path('receipient/<int:receipient_id>/edit/', views.editReceipent, name="edit_recepient"),
    path('receipient/<int:receipient_id>/delete/', views.deleteRecipient, name="delete_recipient"),
    
    # Group Management
    path('group/create/', views.create_group, name='create_group'),
    path('group/edit/<int:group_id>/', views.edit_group, name='edit_group'),
    path('group/delete/<int:group_id>/', views.delete_group, name='delete_group'),

    path('templates/', include('EmailTemplates.urls')),
]
