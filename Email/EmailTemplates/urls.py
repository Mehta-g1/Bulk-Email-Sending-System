from django.urls import path, include
from . import views
urlpatterns = [
    path('',views.Templates, name='templates'),
    path('primary/<int:id>',views.MakePrimary, name='primary'),
    path('view/<int:id>', views.viewTemplate, name='viewTemplate'),
    path('edit/<int:id>', views.editTemplate, name='editTemplate'),
    path('delete/<int:id>',views.deleteTemplate, name='deleteTemplate'),
    path('create/',views.createTemplate, name='createTemplate'),
]