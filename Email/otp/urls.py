from django.urls import path
from . import views

urlpatterns = [
    path('send/', views.send_otp_view, name='send_otp'),
    path('verify/', views.verify_otp_view, name='verify_otp'),
]
