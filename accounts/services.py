from .models import Notification

def create_notification(user, notification_type, title, message, icon=None, link=None):
    """
    Crée une notification pour un utilisateur
    
    Args:
        user: L'utilisateur qui recevra la notification
        notification_type: Le type de notification (voir les choix dans le modèle)
        title: Le titre de la notification
        message: Le message détaillé
        icon: L'icône FontAwesome à utiliser (sans le préfixe 'fa-')
        link: Lien optionnel vers une page liée à la notification
    
    Returns:
        La notification créée
    """
    # Déterminer l'icône par défaut en fonction du type de notification
    if not icon:
        icon_mapping = {
            'transfer_sent': 'paper-plane',
            'transfer_received': 'download',
            'deposit': 'plus-circle',
            'withdrawal': 'minus-circle',
            'profile_update': 'user-edit',
            'account_security': 'shield-alt',
            'bill_payment': 'file-invoice-dollar',
            'system': 'bell'
        }
        icon = icon_mapping.get(notification_type, 'bell')
    
    notification = Notification.objects.create(
        user=user,
        notification_type=notification_type,
        title=title,
        message=message,
        icon=icon,
        link=link
    )
    
    return notification
