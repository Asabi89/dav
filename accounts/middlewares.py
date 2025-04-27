from django.utils.deprecation import MiddlewareMixin
from django.contrib import messages
import os

class SMSSimulatorMiddleware(MiddlewareMixin):
    """Middleware pour afficher les codes de vérification simulés."""
    
    def process_request(self, request):
        # Vérifier si l'utilisateur est authentifié et si le simulateur est activé
        if request.user.is_authenticated and os.environ.get('SMS_SIMULATOR', 'True').lower() == 'true':
            # Vérifier si nous sommes sur la page de vérification
            if request.path == '/accounts/verify-phone/':
                from accounts.models import UserVerification
                
                # Récupérer le dernier code de vérification non utilisé
                verification = UserVerification.objects.filter(
                    user=request.user,
                    is_used=False
                ).order_by('-created_at').first()
                
                if verification:
                    # Ajouter un message avec le code
                    messages.info(
                        request, 
                        f"Mode simulateur: Votre code de vérification est {verification.code}"
                    )
        
        return None
