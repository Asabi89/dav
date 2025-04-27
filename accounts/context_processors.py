def notifications_processor(request):
    """Ajoute le nombre de notifications non lues au contexte global"""
    unread_notifications_count = 0
    notifications = []
    
    if request.user.is_authenticated:
        from .models import Notification
        notifications = Notification.objects.filter(user=request.user).order_by('-created_at')[:5]
        unread_notifications_count = Notification.objects.filter(user=request.user, read=False).count()
    
    return {
        'unread_notifications_count': unread_notifications_count,
        'notifications': notifications,
    }
