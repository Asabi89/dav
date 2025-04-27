from django.core.management.base import BaseCommand
import os
import dotenv

class Command(BaseCommand):
    help = 'Active ou désactive le simulateur SMS'

    def add_arguments(self, parser):
        parser.add_argument(
            '--enable',
            action='store_true',
            help='Active le simulateur SMS',
        )
        parser.add_argument(
            '--disable',
            action='store_true',
            help='Désactive le simulateur SMS',
        )

    def handle(self, *args, **options):
        # Charger le fichier .env s'il existe
        dotenv_file = os.path.join(os.getcwd(), '.env')
        if os.path.isfile(dotenv_file):
            dotenv.load_dotenv(dotenv_file)
        
        if options['enable']:
            os.environ['SMS_SIMULATOR'] = 'True'
            self.stdout.write(self.style.SUCCESS('Simulateur SMS activé'))
            
            # Mettre à jour le fichier .env
            if os.path.isfile(dotenv_file):
                dotenv.set_key(dotenv_file, 'SMS_SIMULATOR', 'True')
        
        elif options['disable']:
            os.environ['SMS_SIMULATOR'] = 'False'
            self.stdout.write(self.style.SUCCESS('Simulateur SMS désactivé'))
            
            # Mettre à jour le fichier .env
            if os.path.isfile(dotenv_file):
                dotenv.set_key(dotenv_file, 'SMS_SIMULATOR', 'False')
        
        else:
            # Afficher l'état actuel
            simulator_status = os.environ.get('SMS_SIMULATOR', 'True')
            self.stdout.write(f'État actuel du simulateur SMS: {"Activé" if simulator_status.lower() == "true" else "Désactivé"}')


#python manage.py toggle_sms_simulator --enable
