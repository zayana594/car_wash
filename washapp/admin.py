from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import *

class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'user_type', 'phone', 'date_joined')
    list_filter = ('user_type', 'is_staff', 'is_active')
    fieldsets = UserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('user_type', 'phone', 'address', 'profile_picture')}),
    )

admin.site.register(User, CustomUserAdmin)
admin.site.register(ServiceCategory)
admin.site.register(Service)
admin.site.register(ServiceProvider)
admin.site.register(Booking)
admin.site.register(Cart)
admin.site.register(Review)
admin.site.register(Payment)