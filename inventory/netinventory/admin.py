from django.contrib import admin
from django.contrib.admin import site as admin_site
from django.contrib.auth.models import User
from .models import *
from django.contrib.auth.admin import User

admin_site.site_header = 'NetInventory Administration'
admin_site.site_title = 'NetInventory'



admin.site.register(Nodes)


class ProfileAdmin(admin.ModelAdmin):
    filter_horizontal = ("groups", "user_permissions")