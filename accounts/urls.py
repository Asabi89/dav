from django.urls import path
from . import views


urlpatterns = [
    path('', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    # Autres URLs existantes
   
    path('send-verification-code/', views.send_verification_code_view, name='send_verification_code'),
    path('verify-phone/', views.verify_phone_view, name='verify_phone'),
    path('resend-verification-code/', views.resend_verification_code_view, name='resend_verification_code'),
    path('phone-auth/', views.phone_auth_view, name='phone_auth'),
    path('verify-inactive-user/', views.verify_inactive_user_view, name='verify_inactive_user'),
   
    path('settings/', views.settings, name='settings'),
    path('contact/', views.contact_view, name='contact'),
    path('preferences/', views.preferences, name='preferences'),
    path('delete-account/', views.delete_account, name='delete_account'),
    path('delete-account/confirm/', views.delete_account_confirm, name='delete_account_confirm'),

  
    path('set-pin/', views.set_pin_view, name='set_pin'),
    path('verify-pin/', views.verify_pin_view, name='verify_pin'),
    
    path('security/', views.security_view, name='security'),
    path('referral/', views.referral_view, name='referral'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('logout/', views.logout_view, name='logout'),
    
    path('notifications/', views.notifications_view, name='notifications'),
    path('notifications/mark-read/<int:notification_id>/', views.mark_notification_read, name='mark_notification_read'),
    path('notifications/mark-all-read/', views.mark_all_read, name='mark_all_read'),
    path('notifications/delete/<int:notification_id>/', views.delete_notification, name='delete_notification'),
    path('notifications/clear-all/', views.clear_all_notifications, name='clear_all_notifications'),
    path('confirm-operation/', views.confirm_operation_view, name='confirm_operation'),

    path('profile/', views.profile_detail_view, name='profile_detail'),
    path('profile/edit/', views.profile_edit_view, name='profile_edit'),
    # Assurez-vous que ces URLs existent ou ajoutez-les
    path('password/change/', views.password_change_view, name='password_change'),
    path('settings/two-factor/', views.two_factor_settings_view, name='two_factor_settings'),
    path('settings/notifications/', views.notification_settings_view, name='notification_settings'),
]
