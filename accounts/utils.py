import os
import logging
from twilio.rest import Client
from django.conf import settings
from importlib import import_module  # Ajoutez cette ligne

# Configuration du logger
logger = logging.getLogger(__name__)

def send_verification_sms(phone_number, code):
    """
    Envoie un SMS de vérification avec le code fourni.
    Retourne un tuple (success, result) où:
    - success est un booléen indiquant si l'envoi a réussi
    - result est soit l'ID du message Twilio, soit un message d'erreur
    """
    # Récupérer les informations d'identification Twilio
    twilio_account_sid = os.environ.get('TWILIO_ACCOUNT_SID', settings.TWILIO_ACCOUNT_SID if hasattr(settings, 'TWILIO_ACCOUNT_SID') else None)
    twilio_auth_token = os.environ.get('TWILIO_AUTH_TOKEN', settings.TWILIO_AUTH_TOKEN if hasattr(settings, 'TWILIO_AUTH_TOKEN') else None)
    twilio_phone_number = os.environ.get('TWILIO_PHONE_NUMBER', settings.TWILIO_PHONE_NUMBER if hasattr(settings, 'TWILIO_PHONE_NUMBER') else None)
    
    # Vérifier si le mode simulation est activé
    use_simulator = os.environ.get('SMS_SIMULATOR', 'True').lower() == 'true'
    
    # Si le mode simulation est activé ou si les informations Twilio sont manquantes
    if use_simulator or not all([twilio_account_sid, twilio_auth_token, twilio_phone_number]):
        # Simuler l'envoi du SMS
        logger.info(f"[SMS SIMULATOR] Envoi d'un SMS à {phone_number} avec le code: {code}")
        
        # Vous pouvez également stocker le code dans un fichier temporaire pour référence
        simulator_dir = os.path.join(settings.BASE_DIR, 'sms_simulator')
        os.makedirs(simulator_dir, exist_ok=True)
        
        # Utilisez django.utils.timezone directement au lieu de import_module
        from django.utils import timezone
        
        with open(os.path.join(simulator_dir, f"{phone_number.replace('+', '')}.txt"), 'w') as f:
            f.write(f"Code de vérification: {code}\nHorodatage: {timezone.now()}")
        
        return True, "SIMULATED_SMS_SID"
    
    # Si nous arrivons ici, nous utilisons Twilio pour l'envoi réel
    try:
        client = Client(twilio_account_sid, twilio_auth_token)
        message = client.messages.create(
            body=f"Votre code de vérification OPay est: {code}",
            from_=twilio_phone_number,
            to=phone_number
        )
        return True, message.sid
    except Exception as e:
        logger.error(f"Erreur lors de l'envoi du SMS via Twilio: {str(e)}")
        # En cas d'échec, revenir au simulateur
        logger.info(f"[SMS SIMULATOR - FALLBACK] Envoi d'un SMS à {phone_number} avec le code: {code}")
        return False, f"Erreur Twilio: {str(e)}. Code de vérification: {code}"
