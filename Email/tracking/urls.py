from django.urls import path
from . import views

urlpatterns = [
    path('open/<uuid:tracking_id>/', views.track_open, name='track_open'),
    path('click/<uuid:tracking_id>/', views.track_click, name='track_click'),
]
