from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils import translation
from django.conf import settings
from django.db.models import Count
from patients.models import Patient
from visits.models import Visit
from backup.views import check_auto_backup
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme


def _safe_redirect_target(request):
    target = request.META.get('HTTP_REFERER')
    if target and url_has_allowed_host_and_scheme(
        target,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return target
    return 'dashboard'


def _set_language_cookie(response, lang):
    response.set_cookie(
        settings.LANGUAGE_COOKIE_NAME,
        lang,
        secure=settings.CSRF_COOKIE_SECURE,
        samesite='Lax',
    )

@login_required
def dashboard(request):
    # 1. Auto Backup Check
    if request.user.role == 'doctor':
        check_auto_backup()
    
    # 2. Language Enforcement Logic
    # If no language is in session, we set it from user profile
    if 'django_language' not in request.session:
        user_lang = request.user.language_preference
        
        # If user has NO preference yet (new user), set by role
        if not user_lang:
            user_lang = 'mr' if request.user.role == 'staff' else 'en'
            request.user.language_preference = user_lang
            request.user.save()
        
        translation.activate(user_lang)
        request.session['django_language'] = user_lang
        response = redirect('dashboard')
        _set_language_cookie(response, user_lang)
        return response

    # 3. Data Processing
    today = timezone.now().date()
    now = timezone.now()
    twelve_hours_ago = now - timezone.timedelta(hours=12)
    
    Visit.objects.filter(status='pending', visited_on__lt=twelve_hours_ago).update(status='unexamined')
    
    today_visits = Visit.objects.filter(visited_on__date=today, status='completed')
    pending_visits = Visit.objects.filter(status='pending', visited_on__gte=twelve_hours_ago).order_by('visited_on')
    recent_patients = Patient.objects.all().order_by('-registered_on')[:5]
    village_stats = Patient.objects.values('village').annotate(count=Count('id')).order_by('-count')[:5]
    
    context = {
        'today_visit_count': today_visits.count(),
        'pending_visits': pending_visits,
        'recent_visits': today_visits.order_by('-visited_on')[:10],
        'recent_patients': recent_patients,
        'village_stats': village_stats,
    }
    
    template = 'dashboard/doctor_dashboard.html' if request.user.role == 'doctor' else 'dashboard/staff_dashboard.html'
    return render(request, template, context)

@login_required
def set_language_pref(request):
    if request.method == 'POST':
        lang = request.POST.get('language')
        if lang in ['en', 'mr']:
            # Save to user profile (Persistence)
            request.user.language_preference = lang
            request.user.save()
            
            # Set in current session
            request.session['django_language'] = lang
            translation.activate(lang)
            
            response = redirect(_safe_redirect_target(request))
            _set_language_cookie(response, lang)
            return response
            
    return redirect('dashboard')
