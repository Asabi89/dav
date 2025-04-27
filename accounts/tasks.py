from celery import shared_task
from django.contrib.auth import get_user_model
from .services import create_notification

User = get_user_model()

@shared_task
def send_inactive_user_reminder():
    """Envoie une notification aux utilisateurs inactifs depuis plus de 30 jours"""
    from datetime import timedelta
    from django.utils import timezone
    
    # Trouver les utilisateurs inactifs depuis 30 jours
    inactive_threshold = timezone.now() - timedelta(days=30)
    inactive_users = User.objects.filter(last_login__lt=inactive_threshold)
    
    for user in inactive_users:
        create_notification(
            user=user,
            notification_type='system',
            title="Votre compte est inactif",
            message="Nous avons remarqué que vous n'avez pas utilisé votre compte OPay depuis plus de 30 jours. Connectez-vous pour profiter de nos services!",
            icon="user-clock"
        )
    
    return f"Notifications envoyées à {inactive_users.count()} utilisateurs inactifs"

@shared_task
def send_security_tips():
    """Envoie périodiquement des conseils de sécurité à tous les utilisateurs"""
    users = User.objects.filter(is_active=True)
    
    security_tips = [
        "N'oubliez pas de changer régulièrement votre mot de passe pour renforcer la sécurité de votre compte.",
        "Activez l'authentification à deux facteurs pour une protection supplémentaire de votre compte.",
        "Ne partagez jamais vos informations de connexion avec qui que ce soit, même s'ils prétendent être du support OPay.",
        "Vérifiez régulièrement votre historique de transactions pour détecter toute activité suspecte."
    ]
    
    import random
    tip = random.choice(security_tips)
    
    for user in users:
        create_notification(
            user=user,
            notification_type='account_security',
            title="Conseil de sécurité",
            message=tip,
            icon="shield-alt"
        )
    
    return f"Conseils de sécurité envoyés à {users.count()} utilisateurs"
