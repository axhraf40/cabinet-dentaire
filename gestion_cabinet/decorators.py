from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps
from django.core.exceptions import PermissionDenied

def role_required(roles):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.error(request, "Veuillez vous connecter pour accéder à cette page.")
                return redirect('login')
            
            if not any(hasattr(request.user, f'{role.lower()}_profile') for role in roles):
                messages.error(request, "Vous n'avez pas les permissions nécessaires pour accéder à cette page.")
                return redirect('dashboard')
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator

def patient_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, "Veuillez vous connecter pour accéder à cette page.")
            return redirect('login')
        
        if not hasattr(request.user, 'patient_profile'):
            messages.error(request, "Accès réservé aux patients.")
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def dentiste_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, "Veuillez vous connecter pour accéder à cette page.")
            return redirect('login')
        
        if not hasattr(request.user, 'dentiste_profile'):
            messages.error(request, "Accès réservé aux dentistes.")
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def secretaire_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, "Veuillez vous connecter pour accéder à cette page.")
            return redirect('login')
        
        if not hasattr(request.user, 'secretaire_profile'):
            messages.error(request, "Accès réservé aux secrétaires.")
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return _wrapped_view 