from django.contrib import admin
from . import models
# Register your models here.
admin.site.register(models.emailUsers)
admin.site.register(models.Receipent)
admin.site.register(models.reset_link)
admin.site.register(models.UserFiles)

admin.site.register(models.Receipent_Group)