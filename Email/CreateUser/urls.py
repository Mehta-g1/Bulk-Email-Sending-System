from django.urls import path, include
from . import views
urlpatterns = [
    path('',views.Login, name='Login'),
    path("auth/", views.Authenticate, name="auth"),
    path('signUp/',views.signUp, name='signUp'),
    path('signing-up/', views.signingUp, name="signing-up"),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('logout/',views.logout, name='logout'),
    path('send-mail/', views.sendMail, name="send-mail"),
    path('viewProfile', views.profile, name='profile'),

]