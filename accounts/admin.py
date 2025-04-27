from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from .models import User, UserVerification, UserSecurityQuestion

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'phone_number', 'profile_picture', 'date_of_birth')}),
        (_('Security'), {'fields': ('pin_code', 'is_verified')}),
        (_('Preferences'), {'fields': ('language', 'dark_mode', 'enable_notifications')}),
        (_('Referral'), {'fields': ('referral_code', 'referred_by')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'phone_number', 'password1', 'password2'),
        }),
    )
    list_display = ('email', 'phone_number', 'first_name', 'last_name', 'is_staff', 'is_verified')
    search_fields = ('email', 'phone_number', 'first_name', 'last_name')
    ordering = ('email',)


@admin.register(UserVerification)
class UserVerificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'code', 'created_at', 'expires_at', 'is_used')
    search_fields = ('user__email', 'user__phone_number', 'code')
    list_filter = ('is_used', 'created_at')


@admin.register(UserSecurityQuestion)
class UserSecurityQuestionAdmin(admin.ModelAdmin):
    list_display = ('user', 'question')
    search_fields = ('user__email', 'question')
