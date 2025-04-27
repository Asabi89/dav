from django.utils import timezone

class UserActivityMiddleware:
    """Middleware pour suivre l'activité des utilisateurs."""
    
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        response = self.get_response(request)
        
        # Mettre à jour la dernière activité pour les utilisateurs authentifiés
        if request.user.is_authenticated:
            # Ne pas mettre à jour pour les requêtes AJAX ou statiques
            if not request.headers.get('X-Requested-With') == 'XMLHttpRequest' and not request.path.startswith('/static/'):
                request.user.last_activity = timezone.now()
                request.user.save(update_fields=['last_activity'])
                
        return response
