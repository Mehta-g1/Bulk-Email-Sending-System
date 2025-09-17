from django.urls import path, include
from . import views


urlpatterns = [
    path('login/',views.Login, name='Login'),
    path('signUp/',views.signUp, name='signUp'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('logout/',views.logout, name='logout'),
    path('send-mail/', views.sendMail, name="send-mail"),
    path('viewProfile', views.profile, name='profile'),
    path('edit-profile/', views.edit_profile, name='edit_profile'),
    path('change-password/', views.change_password, name='change_password'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('reset-password/<str:token>/', views.reset_password, name='reset_password'),
    path('edit-profile-process/',views.edit_profile_process, name='edit_profile_process'),
    path('receipient/add/', views.addReceipent, name="add_recepient"),
    path('receipient/<int:receipient_id>/', views.viewReceipent, name="view_recepient"),
    path('receipient/<int:receipient_id>/edit/', views.editReceipent, name="edit_recepient"),
    path('receipient/<int:receipient_id>/delete/', views.deleteRecipient, name="delete_recipient"),
    path('templates/', include('EmailTemplates.urls')),
]
