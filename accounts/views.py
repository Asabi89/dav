from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.utils.crypto import get_random_string
from django.urls import reverse
from django.http import JsonResponse
from datetime import timedelta
import os 
from .utils import send_verification_sms
from twilio.rest import Client
from .forms import (
    CustomUserCreationForm, CustomAuthenticationForm, PhoneVerificationForm,
    PinCodeForm, UserProfileForm, SecurityQuestionForm
)
from .models import User, UserVerification, UserSecurityQuestion,PhoneNumber
from .utils import  send_verification_sms
from django.views.decorators.csrf import csrf_protect 
import time



def register_view(request):
    """User registration view."""
    if request.method == 'POST':
        # Créer une copie des données POST pour les modifier si nécessaire
        post_data = request.POST.copy()
        
        # S'assurer que le numéro de téléphone est correctement formaté
        phone_number = post_data.get('phone_number', '')
        if phone_number and not phone_number.startswith('+'):
            phone_number = '+' + phone_number
            post_data['phone_number'] = phone_number
            
        form = CustomUserCreationForm(post_data)
        
        if form.is_valid():
            try:
                user = form.save(commit=False)
                user.is_active = True  # User is active but not verified
                user.is_verified = False
                
                # Check referral code
                referral_code = form.cleaned_data.get('referral_code')
                if referral_code:
                    try:
                        referrer = User.objects.get(referral_code=referral_code)
                        user.referred_by = referrer
                    except User.DoesNotExist:
                        messages.warning(request, "Code de parrainage invalide.")
                
                user.save()
                
                # Generate verification code
                code = get_random_string(length=6, allowed_chars='0123456789')
                expires_at = timezone.now() + timedelta(minutes=10)
                
                verification = UserVerification.objects.create(
                    user=user,
                    code=code,
                    expires_at=expires_at
                )
                
                # Stocker le numéro de téléphone dans la session pour la vérification
                request.session['phone_verification_number'] = user.phone_number
                
                # Envoyer le SMS avec le code de vérification
                success, result = send_verification_sms(user.phone_number, code)
                if success:
                    messages.success(
                        request,
                        "Compte créé avec succès! Un code de vérification a été envoyé à votre numéro de téléphone."
                    )
                    verification.sms_sid = result
                    verification.save()
                else:
                    messages.warning(
                        request,
                        f"Compte créé, mais impossible d'envoyer le SMS: {result}. Votre code est: {code}"
                    )
                
                # Log the user in
                login(request, user)
                
                # Redirect to verification page
                return redirect('verify_phone')
            except Exception as e:
                # Catch any exceptions and display them
                messages.error(request, f"Une erreur s'est produite: {str(e)}")
                print("Exception during registration:", str(e))
        else:
            # Debug form errors
            print("Form is invalid. Errors:", form.errors)
            # Add form errors to messages for visibility
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"Erreur dans le champ {field}: {error}")
    else:
        form = CustomUserCreationForm()
    
    # Always pass the form to the template, even if it has errors
    return render(request, 'accounts/register.html', {'form': form})
def login_view(request):
    """User login view."""
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        
        # Récupérer l'identifiant (email ou téléphone)
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        # Vérifier si l'identifiant est un numéro de téléphone
        is_phone = username.startswith('+') or username.isdigit()
        
        if is_phone:
            # Formater le numéro de téléphone si nécessaire
            if not username.startswith('+'):
                username = '+' + username
                
            # Chercher l'utilisateur par numéro de téléphone
            try:
                user = User.objects.get(phone_number=username)
                # Authentifier avec l'email de l'utilisateur
                user = authenticate(request, username=user.email, password=password)
                
                if user is not None:
                    # Vérifier si l'utilisateur est inactif depuis 3 jours
                    if user.is_inactive_for_long(days=3):
                        # Stocker l'ID de l'utilisateur dans la session pour la vérification
                        request.session['inactive_user_id'] = user.id
                        # Envoyer un code de vérification
                        return redirect('verify_inactive_user')
                    
                    # Connexion normale
                    login(request, user)
                    
                    # Log activity
                    log_user_activity(user, 'login', 'Connexion réussie', request)
                    
                    # Vérifier si l'utilisateur est vérifié
                    if not user.is_verified:
                        # Stocker le numéro de téléphone dans la session pour la vérification
                        request.session['phone_verification_number'] = username
                        return redirect('verify_phone')
                    
                    # Vérifier si le PIN est défini
                    if not user.pin_code:
                        return redirect('set_pin')
                    
                    # Rediriger vers le tableau de bord
                    return redirect('dashboard')
                else:
                    messages.error(request, "Numéro de téléphone ou mot de passe invalide.")
            except User.DoesNotExist:
                messages.error(request, "Aucun compte associé à ce numéro de téléphone.")
        else:
            # Authentification standard par email
            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                # Vérifier si l'utilisateur est inactif depuis 3 jours
                if user.is_inactive_for_long(days=3):
                    # Stocker l'ID de l'utilisateur dans la session pour la vérification
                    request.session['inactive_user_id'] = user.id
                    # Envoyer un code de vérification
                    return redirect('verify_inactive_user')
                
                # Connexion normale
                login(request, user)
                
                # Log activity
                log_user_activity(user, 'login', 'Connexion réussie', request)
                
                # Vérifier si l'utilisateur est vérifié
                if not user.is_verified:
                    # Si l'utilisateur a un numéro de téléphone, le stocker dans la session
                    if user.phone_number:
                        request.session['phone_verification_number'] = user.phone_number
                    return redirect('verify_phone')
                
                # Vérifier si le PIN est défini
                if not user.pin_code:
                    return redirect('set_pin')
                
                # Rediriger vers le tableau de bord
                return redirect('dashboard')
            else:
                messages.error(request, "Email ou mot de passe invalide.")
    else:
        form = CustomAuthenticationForm()
    
    return render(request, 'accounts/login.html', {'form': form})


from django.core.mail import send_mail
from django.conf import settings

def verify_inactive_user_view(request):
    """Vérification des utilisateurs inactifs depuis longtemps."""
    # Récupérer l'ID de l'utilisateur depuis la session
    user_id = request.session.get('inactive_user_id')
    if not user_id:
        messages.error(request, "Session expirée. Veuillez vous reconnecter.")
        return redirect('login')
    
    # Récupérer l'utilisateur
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        messages.error(request, "Utilisateur non trouvé. Veuillez vous reconnecter.")
        return redirect('login')
    
    if request.method == 'POST':
        # Vérifier le code
        verification_code = request.POST.get('verification_code')
        
        # Récupérer la vérification depuis la base de données
        verification = UserVerification.objects.filter(
            user=user,
            code=verification_code,
            is_used=False
        ).order_by('-created_at').first()
        
        if verification and verification.is_valid():
            # Marquer le code comme utilisé
            verification.is_used = True
            verification.save()
            
            # Mettre à jour la dernière activité
            user.last_activity = timezone.now()
            user.save()
            
            # Connecter l'utilisateur
            login(request, user)
            
            # Nettoyer la session
            if 'inactive_user_id' in request.session:
                del request.session['inactive_user_id']
            
            messages.success(request, "Vérification réussie! Bienvenue de retour.")
            
            # Vérifier si le PIN est défini
            if not user.pin_code:
                return redirect('set_pin')
            
            # Rediriger vers le tableau de bord
            return redirect('dashboard')
        else:
            messages.error(request, "Code de vérification invalide ou expiré.")
    else:
        # Générer un code de vérification
        code = get_random_string(length=6, allowed_chars='0123456789')
        expires_at = timezone.now() + timedelta(minutes=10)
        
        # Créer la vérification
        verification = UserVerification.objects.create(
            user=user,
            code=code,
            expires_at=expires_at
        )
        
        # Déterminer la méthode de vérification (email ou SMS)
        verification_method = request.GET.get('method', 'email')
        
        if verification_method == 'phone' and user.phone_number:
            # Envoyer un SMS
            success, result = send_verification_sms(user.phone_number, code)
            if success:
                messages.success(request, "Un code de vérification a été envoyé à votre numéro de téléphone.")
                verification.sms_sid = result
                verification.save()
            else:
                messages.error(request, f"Impossible d'envoyer le SMS: {result}")
                # Proposer l'email comme alternative
                return redirect('verify_inactive_user')
        else:
            # Envoyer un email
            try:
                send_mail(
                    'Vérification de votre compte OPay',
                    f'Bonjour,\n\nVotre compte OPay a été inactif pendant plus de 3 mois. '
                    f'Pour des raisons de sécurité, veuillez vérifier votre identité en utilisant ce code: {code}\n\n'
                    f'Ce code est valable pendant 10 minutes.\n\n'
                    f'L\'équipe OPay',
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                    fail_silently=False,
                )
                messages.success(request, "Un code de vérification a été envoyé à votre adresse email.")
            except Exception as e:
                messages.error(request, f"Impossible d'envoyer l'email: {str(e)}")
                return redirect('login')
    
    # Déterminer la méthode utilisée pour l'affichage
    verification_method = request.GET.get('method', 'email')
    contact_info = user.email if verification_method == 'email' else user.phone_number
    
    return render(request, 'accounts/verify_inactive_user.html', {
        'verification_method': verification_method,
        'contact_info': contact_info
    })



@login_required
def set_pin_view(request):
    """Set PIN code view."""
    user = request.user
    
    # If PIN is already set, redirect to dashboard
    if user.pin_code:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = PinCodeForm(request.POST)
        if form.is_valid():
            pin_code = form.cleaned_data.get('pin_code')
            
            # Vérifier que le PIN contient uniquement des chiffres
            if not pin_code.isdigit():
                messages.error(request, "Le code PIN doit contenir uniquement des chiffres.")
                return render(request, 'accounts/set_pin.html', {'form': form})
            
            # Set PIN code
            user.pin_code = pin_code
            user.save()
            
            messages.success(request, "Code PIN défini avec succès!")
            
            # Redirect to dashboard
            return redirect('dashboard')
        else:
            # Afficher les erreurs du formulaire
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"Erreur: {error}")
    else:
        form = PinCodeForm()
    
    return render(request, 'accounts/set_pin.html', {'form': form})

@login_required
def verify_pin_view(request):
    """Verify PIN code for sensitive operations."""
    if request.method == 'POST':
        form = PinCodeForm(request.POST)
        if form.is_valid():
            pin_code = form.cleaned_data.get('pin_code')
            
            if request.user.pin_code == pin_code:
                # Set session flag for sensitive operations
                request.session['pin_verified'] = True
                request.session['pin_verified_at'] = time.time()  # Utiliser time.time() au lieu de timezone.now().timestamp()
                
                # Log activity
                log_user_activity(request.user, 'security_update', 'Vérification du code PIN', request)
                
                # Redirect to the next page (stored in session)
                next_url = request.session.get('next_url', 'dashboard')
                if 'next_url' in request.session:
                    del request.session['next_url']
                
                return redirect(next_url)
            else:
                messages.error(request, "Code PIN incorrect.")
    else:
        form = PinCodeForm()
        
        # Store next URL in session
        next_url = request.GET.get('next', 'dashboard')
        request.session['next_url'] = next_url
    
    return render(request, 'accounts/verify_pin.html', {'form': form})

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import UserProfileForm
from accounts.services import create_notification
@login_required
def profile_detail_view(request):
    """Vue de détail du profil utilisateur."""
    # Récupérer l'utilisateur actuel
    user = request.user
    
    # Récupérer les activités récentes
    recent_activities = UserActivity.objects.filter(user=user).order_by('-timestamp')[:5]
    
    # Compter les questions de sécurité
    security_questions_count = UserSecurityQuestion.objects.filter(user=user).count()
    
    context = {
        'user': user,
        'recent_activities': recent_activities,
        'security_questions_count': security_questions_count
    }
    
    return render(request, 'accounts/profile_detail.html', context)

@login_required
def profile_edit_view(request):
    """Vue de modification du profil utilisateur."""
    # Récupérer l'utilisateur actuel
    user = request.user
    
    if request.method == 'POST':
        # Traiter le formulaire soumis
        form = UserProfileForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            # Sauvegarder les modifications
            form.save()
            
            # Enregistrer l'activité
            log_user_activity(user, 'profile_update', 'Profil mis à jour', request)
            
            # Créer une notification pour l'utilisateur
            create_notification(
                user=user,
                notification_type='profile_update',
                title="Profil mis à jour",
                message="Votre profil a été mis à jour avec succès. Les modifications ont été enregistrées.",
                icon="user-edit"
            )
            
            messages.success(request, "Profil mis à jour avec succès!")
            return redirect('profile_detail')
    else:
        # Afficher le formulaire initial
        form = UserProfileForm(instance=user)
    
    return render(request, 'accounts/profile_edit.html', {'form': form})



from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from .forms import PinCodeForm, SecurityQuestionForm
from .models import UserSecurityQuestion, UserActivity

User = get_user_model()

def log_user_activity(user, activity_type, description=None, request=None):
    """
    Log user activity.
    
    Args:
        user: User object
        activity_type: Type of activity (from UserActivity.ACTIVITY_TYPES)
        description: Optional description
        request: Optional request object to extract IP address
    """
    # Get IP address if request is provided
    ip_address = None
    if request:
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip_address = x_forwarded_for.split(',')[0]
        else:
            ip_address = request.META.get('REMOTE_ADDR')
    
    # Create activity log
    if not description:
        # Use default description based on activity type
        activity_dict = dict(UserActivity.ACTIVITY_TYPES)
        description = activity_dict.get(activity_type, 'Activité utilisateur')
    
    UserActivity.objects.create(
        user=user,
        activity_type=activity_type,
        description=description,
        ip_address=ip_address
    )

@login_required
def security_view(request):
    """Security settings view."""
    user = request.user
    
    # Get recent activities
    recent_activities = UserActivity.objects.filter(user=user).order_by('-timestamp')[:5]
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'change_pin':
            form = PinCodeForm(request.POST)
            if form.is_valid():
                pin_code = form.cleaned_data.get('pin_code')
                
                # Vérifier que le PIN contient uniquement des chiffres
                if not pin_code.isdigit():
                    messages.error(request, "Le code PIN doit contenir uniquement des chiffres.")
                    return redirect('security')
                
                # Update PIN code
                user.pin_code = pin_code
                user.save()
                
                # Log activity
                log_user_activity(user, 'pin_change', 'Changement de code PIN', request)
                
                messages.success(request, "Code PIN mis à jour avec succès!")
                return redirect('security')
                
        elif action == 'add_question':
            form = SecurityQuestionForm(request.POST)
            if form.is_valid():
                question = form.save(commit=False)
                question.user = user
                question.save()
                
                # Log activity
                log_user_activity(user, 'security_update', 'Ajout d\'une question de sécurité', request)
                
                messages.success(request, "Question de sécurité ajoutée avec succès!")
                return redirect('security')
                
        elif action == 'delete_question':
            question_id = request.POST.get('question_id')
            try:
                question = UserSecurityQuestion.objects.get(id=question_id, user=user)
                question.delete()
                
                # Log activity
                log_user_activity(user, 'security_update', 'Suppression d\'une question de sécurité', request)
                
                messages.success(request, "Question de sécurité supprimée avec succès!")
            except UserSecurityQuestion.DoesNotExist:
                messages.error(request, "Question de sécurité introuvable.")
            return redirect('security')
    else:
        pin_form = PinCodeForm()
        question_form = SecurityQuestionForm()
    
    security_questions = UserSecurityQuestion.objects.filter(user=user)
    
    context = {
        'pin_form': pin_form,
        'question_form': question_form,
        'security_questions': security_questions,
        'recent_activities': recent_activities
    }
    
    return render(request, 'accounts/security.html', context)


@login_required
def referral_view(request):
    """Referral program view."""
    user = request.user
    referrals = User.objects.filter(referred_by=user)
    
    context = {
        'referral_code': user.referral_code,
        'referrals': referrals,
        'referral_url': request.build_absolute_uri(reverse('register') + f'?ref={user.referral_code}')
    }
    
    return render(request, 'accounts/referral.html', context)


@login_required
def dashboard_view(request):
    """User dashboard view."""
    user = request.user
    
    # Get user's wallet
    from wallet.models import Wallet
    wallet = Wallet.objects.filter(user=user).first()
    
    # Get recent transactions
    from transactions.models import Transaction
    recent_transactions = Transaction.objects.filter(
        wallet=wallet
    ).order_by('-timestamp')[:2]
    
    context = {
        'wallet': wallet,
        'recent_transactions': recent_transactions,
    }
    
    return render(request, 'accounts/dashboard.html', context)


@login_required
def logout_view(request):
    """Logout view."""
    logout(request)
    messages.success(request, "Vous avez été déconnecté avec succès.")
    return redirect('login')




@csrf_protect
def send_verification_code_view(request):
    """Send verification code to phone."""
    if request.method == 'POST':
        phone_number = request.POST.get('phone_number')
        
        # Assurez-vous que le numéro de téléphone est correctement formaté
        if phone_number and not phone_number.startswith('+'):
            phone_number = '+' + phone_number
        
        # Validation basique du numéro de téléphone
        if not phone_number or len(phone_number) < 10:
            messages.error(request, "Veuillez entrer un numéro de téléphone valide")
            return redirect('phone_login')
        
        # Générer un code de vérification
        code = generate_verification_code()
        expires_at = timezone.now() + timedelta(minutes=10)
        
        # Stocker le code dans la base de données
        # Si l'utilisateur n'est pas encore connu, user sera None
        verification = UserVerification.objects.create(
            user=None,  # Sera mis à jour après la vérification
            code=code,
            expires_at=expires_at
        )
        
        # Stocker le numéro de téléphone dans la session
        request.session['phone_verification_number'] = phone_number
        request.session['phone_verification_id'] = verification.id
        
        # Envoyer le SMS avec le code
        success, result = send_verification_sms(phone_number, code)
        
        if success:
            messages.success(request, "Un code de vérification a été envoyé à votre numéro de téléphone.")
            return redirect('verify_phone')
        else:
            messages.error(request, f"Impossible d'envoyer le SMS: {result}")
            return redirect('phone_login')
    
    return redirect('phone_login')

@login_required
def verify_phone_view(request):
    """Phone verification view."""
    user = request.user
    
    # If user is already verified, redirect to dashboard
    if user.is_verified:
        return redirect('dashboard')
    
    # Vérifier si le mode simulateur est activé
    use_simulator = True  # Par défaut, on active le simulateur
    simulator_code = None
    
    # Récupérer le dernier code de vérification non utilisé
    verification = UserVerification.objects.filter(
        user=user,
        is_used=False
    ).order_by('-created_at').first()
    
    if verification:
        simulator_code = verification.code
    
    if request.method == 'POST':
        form = PhoneVerificationForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data.get('verification_code')
            
            # Check if code is valid
            verification = UserVerification.objects.filter(
                user=user,
                code=code,
                is_used=False
            ).order_by('-created_at').first()
            
            if verification and verification.is_valid():
                # Mark code as used
                verification.is_used = True
                verification.save()
                
                # Mark user as verified
                user.is_verified = True
                user.save()
                
                messages.success(request, "Numéro de téléphone vérifié avec succès!")
                
                # Check if PIN is set
                if not user.pin_code:
                    return redirect('set_pin')
                
                # Redirect to dashboard
                return redirect('dashboard')
            else:
                messages.error(request, "Code de vérification invalide ou expiré.")
    else:
        form = PhoneVerificationForm()
    
    context = {
        'form': form,
        'simulator_active': use_simulator,
        'simulator_code': simulator_code
    }
    
    return render(request, 'accounts/verify_phone.html', context)


def resend_verification_code_view(request):
    """Resend verification code to user's phone."""
    if request.method == 'POST' and request.user.is_authenticated:
        user = request.user
        
        # Generate new verification code
        code = get_random_string(length=6, allowed_chars='0123456789')
        expires_at = timezone.now() + timedelta(minutes=10)
        
        verification = UserVerification.objects.create(
            user=user,
            code=code,
            expires_at=expires_at
        )
        
        # En mode simulateur, on affiche simplement le code
        messages.success(
            request, 
            f"Un nouveau code de vérification a été généré. Utilisez le code affiché sur la page."
        )
    
    # Redirect back to the verify phone page
    return redirect('verify_phone')



# Nouvelle fonction pour l'authentification directe par téléphone
@csrf_protect
def phone_auth_view(request):
    """Authenticate user with phone number."""
    if request.method == 'POST':
        phone_number = request.POST.get('phone_number')
        verification_code = request.POST.get('verification_code')
        
        # Assurez-vous que le numéro de téléphone est correctement formaté
        if phone_number and not phone_number.startswith('+'):
            phone_number = '+' + phone_number
        
        # Vérifier si le code est valide
        try:
            verification = UserVerification.objects.filter(
                code=verification_code,
                is_used=False
            ).order_by('-created_at').first()
            
            if verification and verification.is_valid():
                # Marquer le code comme utilisé
                verification.is_used = True
                verification.save()
                
                # Vérifier si un utilisateur avec ce numéro de téléphone existe
                try:
                    phone_obj = PhoneNumber.objects.get(phone_number=phone_number)
                    user = phone_obj.user
                    
                    # Mettre à jour le statut de vérification
                    user.is_verified = True
                    user.save()
                    
                    # Connecter l'utilisateur
                    login(request, user)
                    
                    messages.success(request, "Connexion réussie!")
                    return redirect('dashboard')
                    
                except PhoneNumber.DoesNotExist:
                    # Créer un nouvel utilisateur avec ce numéro de téléphone
                    # Générer un email aléatoire
                    import uuid
                    random_uuid = uuid.uuid4().hex[:8]
                    email = f"user_{random_uuid}@opay.com"
                    
                    # Créer l'utilisateur
                    user = User.objects.create_user(
                        email=email,
                        phone_number=phone_number,
                        password=get_random_string(length=12),  # Mot de passe aléatoire
                        first_name="Utilisateur",
                        last_name="Temporaire",
                        is_verified=True
                    )
                    
                    # Créer l'enregistrement PhoneNumber
                    PhoneNumber.objects.create(
                        user=user,
                        phone_number=phone_number,
                        verified=True
                    )
                    
                    # Connecter l'utilisateur
                    login(request, user)
                    
                    messages.success(request, "Compte créé avec succès!")
                    return redirect('profile')  # Rediriger vers le profil pour compléter les informations
            else:
                messages.error(request, "Code de vérification invalide ou expiré.")
        except Exception as e:
            messages.error(request, f"Une erreur s'est produite: {str(e)}")
    
    return redirect('phone_login')


# opay_fintech/accounts/utils.py

def log_user_activity(user, activity_type, description=None, request=None):
    """
    Log user activity.
    
    Args:
        user: User object
        activity_type: Type of activity (from UserActivity.ACTIVITY_TYPES)
        description: Optional description
        request: Optional request object to extract IP address
    """
    from .models import UserActivity
    
    # Get IP address if request is provided
    ip_address = None
    if request:
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip_address = x_forwarded_for.split(',')[0]
        else:
            ip_address = request.META.get('REMOTE_ADDR')
    
    # Create activity log
    if not description:
        # Use default description based on activity type
        activity_dict = dict(UserActivity.ACTIVITY_TYPES)
        description = activity_dict.get(activity_type, 'Activité utilisateur')
    
    UserActivity.objects.create(
        user=user,
        activity_type=activity_type,
        description=description,
        ip_address=ip_address
    )



from django.contrib.auth import authenticate, logout
from django.contrib import messages
from django.shortcuts import redirect, render

def delete_account_confirm(request):
    if request.method == 'POST':
        # Récupérer le mot de passe du formulaire
        password = request.POST.get('password', '')
        
        # Vérifier le mot de passe
        user = request.user
        if authenticate(username=user.username, password=password):
            # Mot de passe correct, déconnecter l'utilisateur
            logout(request)
            
            # Supprimer le compte
            user.delete()
            
            messages.success(request, "Votre compte a été supprimé avec succès. Nous espérons vous revoir bientôt!")
            return redirect('home')
        else:
            # Mot de passe incorrect
            messages.error(request, "Mot de passe incorrect. Veuillez réessayer.")
            return redirect('delete_account')
    
    return redirect('delete_account')



from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.urls import reverse
from django.db.models import Q
from .models import Notification

@login_required
def notifications_view(request):
    """Vue principale pour afficher toutes les notifications de l'utilisateur"""
    notifications = Notification.objects.filter(user=request.user)
    unread_count = notifications.filter(read=False).count()
    
    # Filtrage par type si spécifié
    notification_type = request.GET.get('type')
    if notification_type:
        notifications = notifications.filter(notification_type=notification_type)
    
    # Filtrage par statut de lecture si spécifié
    read_status = request.GET.get('read')
    if read_status == 'unread':
        notifications = notifications.filter(read=False)
    elif read_status == 'read':
        notifications = notifications.filter(read=True)
    
    context = {
        'notifications': notifications,
        'unread_count': unread_count,
        'notification_types': Notification.NOTIFICATION_TYPES,
        'current_type': notification_type,
        'current_read_status': read_status,
    }
    
    return render(request, 'accounts/notifications.html', context)

@login_required
def mark_notification_read(request, notification_id):
    """Marquer une notification spécifique comme lue"""
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.mark_as_read()
    
    # Rediriger vers le lien de la notification si disponible
    if notification.link:
        return redirect(notification.link)
    
    # Sinon, retourner à la page des notifications
    return redirect('notifications')

@login_required
def mark_all_read(request):
    """Marquer toutes les notifications comme lues"""
    Notification.objects.filter(user=request.user, read=False).update(read=True)
    
    # Rediriger vers la page précédente si disponible
    next_url = request.GET.get('next', reverse('notifications'))
    return redirect(next_url)

@login_required
def delete_notification(request, notification_id):
    """Supprimer une notification spécifique"""
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.delete()
    
    # Si c'est une requête AJAX, renvoyer une réponse JSON
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'status': 'success'})
    
    # Sinon, rediriger vers la page des notifications
    return redirect('notifications')


@login_required
def clear_all_notifications(request):
    """Supprimer toutes les notifications de l'utilisateur"""
    Notification.objects.filter(user=request.user).delete()
    
    return redirect('notifications')






from django.shortcuts import render

def contact_view(request):
    return render(request, 'accounts/contact.html')


def settings(request):
    return render(request, 'accounts/settings.html')


def preferences(request):
    return render(request, 'accounts/preferences.html')


def delete_account(request):
    return render(request, 'accounts/delete_account.html')

def password_change_view(request):
    return render(request, 'accounts/password_change.html')

def two_factor_settings_view(request):
    return render(request, 'accounts/two_factor_settings.html')


def notification_settings_view(request):
    return render(request, 'accounts/notification_settings.html')   


@login_required
def confirm_operation_view(request):
    """Vue pour confirmer une opération sensible avec le code PIN."""
    if request.method == 'POST':
        form = PinCodeForm(request.POST)
        if form.is_valid():
            pin_code = form.cleaned_data.get('pin_code')
            
            # Récupérer les données de l'opération depuis la session
            operation_type = request.session.get('operation_type')
            operation_data = request.session.get('operation_data', {})
            
            if not operation_type or not operation_data:
                messages.error(request, "Données d'opération invalides ou expirées.")
                return redirect('dashboard')
            
            # Vérifier le PIN
            if request.user.pin_code == pin_code:
                # PIN correct, procéder à l'opération
                if operation_type == 'deposit':
                    # Exécuter le dépôt
                    from wallet.views import process_deposit
                    result = process_deposit(request, operation_data)
                    return result
                
                elif operation_type == 'withdraw':
                    # Exécuter le retrait
                    from wallet.views import process_withdrawal
                    result = process_withdrawal(request, operation_data)
                    return result
                
                elif operation_type == 'transfer':
                    # Exécuter le transfert
                    from wallet.views import process_transfer
                    result = process_transfer(request, operation_data)
                    return result
                
                else:
                    messages.error(request, "Type d'opération non pris en charge.")
                    return redirect('dashboard')
            else:
                # PIN incorrect
                messages.error(request, "Code PIN incorrect.")
    else:
        form = PinCodeForm()
        
        # Récupérer les informations sur l'opération pour l'affichage
        operation_type = request.session.get('operation_type')
        operation_data = request.session.get('operation_data', {})
        
        if not operation_type or not operation_data:
            messages.error(request, "Données d'opération invalides ou expirées.")
            return redirect('dashboard')
    
    # Préparer le contexte pour le template
    context = {
        'form': form,
        'operation_type': operation_type,
        'operation_data': operation_data
    }
    
    return render(request, 'accounts/confirm_operation.html', context)
