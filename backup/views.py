import os
import shutil
import sqlite3
import tempfile
from datetime import datetime
from pathlib import Path
from urllib.parse import urlencode

from django.contrib.auth import logout as auth_logout
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import connections
from django.urls import reverse
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.translation import gettext_lazy as _
from .models import BackupSettings


PIN_MAX_ATTEMPTS = 5
PIN_LOCKOUT_MINUTES = 15
SQLITE_HEADER = b'SQLite format 3\x00'
REQUIRED_RESTORE_TABLES = {
    'accounts_customuser',
    'patients_patient',
    'visits_visit',
    'django_migrations',
    'django_session',
}


def _validation_message(error):
    return ' '.join(error.messages) if hasattr(error, 'messages') else str(error)


def _resolve_backup_dir(raw_path):
    if not raw_path:
        raise ValidationError(_("Backup path is required."))

    candidate = Path(raw_path).expanduser()
    if not candidate.is_absolute():
        raise ValidationError(_("Backup path must be an absolute path."))

    resolved = candidate.resolve(strict=False)
    allowed_roots = [Path(path).expanduser().resolve(strict=False) for path in settings.BACKUP_ALLOWED_ROOTS]
    if not any(resolved == root or root in resolved.parents for root in allowed_roots):
        allowed = ', '.join(str(root) for root in allowed_roots)
        raise ValidationError(_("Backup path must be inside an allowed backup directory: %(allowed)s") % {'allowed': allowed})

    return resolved


def _ensure_backup_directory(raw_path):
    backup_dir = _resolve_backup_dir(raw_path)
    backup_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
    return backup_dir


def _pin_verification_redirect(request):
    query = urlencode({'next': request.get_full_path()})
    return redirect(f"{reverse('verify_pin')}?{query}")


def _is_pin_verified(request, config):
    return (
        request.session.get('security_pin_verified') is True
        and request.session.get('security_pin_version') == str(config.pin_version)
    )


def _safe_next_url(request):
    next_url = request.GET.get('next') or 'backup_manager'
    if url_has_allowed_host_and_scheme(
        next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return next_url
    return 'backup_manager'


def _pin_lockout_seconds(request):
    locked_until = request.session.get('backup_pin_locked_until')
    if not locked_until:
        return 0

    seconds = int(locked_until - timezone.now().timestamp())
    if seconds > 0:
        return seconds

    request.session.pop('backup_pin_locked_until', None)
    return 0


def _record_failed_pin_attempt(request):
    attempts = int(request.session.get('backup_pin_attempts', 0)) + 1
    if attempts >= PIN_MAX_ATTEMPTS:
        request.session['backup_pin_attempts'] = 0
        request.session['backup_pin_locked_until'] = (
            timezone.now() + timezone.timedelta(minutes=PIN_LOCKOUT_MINUTES)
        ).timestamp()
    else:
        request.session['backup_pin_attempts'] = attempts


def _clear_pin_attempts(request):
    request.session.pop('backup_pin_attempts', None)
    request.session.pop('backup_pin_locked_until', None)


def _validate_sqlite_backup(temp_path):
    with temp_path.open('rb') as uploaded:
        if uploaded.read(len(SQLITE_HEADER)) != SQLITE_HEADER:
            raise ValidationError(_("Backup file is not a SQLite database."))

    try:
        connection = sqlite3.connect(temp_path)
        try:
            quick_check = connection.execute('PRAGMA quick_check').fetchone()
            if not quick_check or quick_check[0] != 'ok':
                raise ValidationError(_("Backup file failed SQLite integrity checks."))

            tables = {
                row[0]
                for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
            }
            missing_tables = REQUIRED_RESTORE_TABLES - tables
            if missing_tables:
                raise ValidationError(_("Backup file does not look like a hospital database backup."))
        finally:
            connection.close()
    except sqlite3.DatabaseError:
        raise ValidationError(_("Backup file is not a readable SQLite database."))


def _save_uploaded_backup_to_temp(uploaded_file):
    with tempfile.NamedTemporaryFile(prefix='restore_', suffix='.sqlite3', delete=False) as temp_file:
        for chunk in uploaded_file.chunks():
            temp_file.write(chunk)
        return Path(temp_file.name)


def check_auto_backup():
    """Triggered on doctor's dashboard load to check if 10 days have passed."""
    backup_config = BackupSettings.get_settings()
    now = timezone.now()
    
    if not backup_config.last_backup_date or (now - backup_config.last_backup_date).days >= backup_config.auto_backup_days:
        try:
            backup_dir = _ensure_backup_directory(backup_config.backup_path)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_filename = f"db_backup_{timestamp}.sqlite3"
            backup_full_path = backup_dir / backup_filename
            
            shutil.copy2(settings.DATABASES['default']['NAME'], backup_full_path)
            
            backup_config.last_backup_date = now
            backup_config.save()
            return True, backup_filename
        except Exception as e:
            return False, str(e)
    return False, None

@login_required
def verify_pin(request):
    if request.user.role != 'doctor':
        return redirect('dashboard')
        
    if request.method == 'POST':
        locked_seconds = _pin_lockout_seconds(request)
        if locked_seconds:
            messages.error(request, f"Too many incorrect attempts. Try again in {locked_seconds // 60 + 1} minutes.")
            return render(request, 'backup/pin_verify.html')

        entered_pin = request.POST.get('pin', '')
        config = BackupSettings.get_settings()
        if config.check_security_pin(entered_pin):
            request.session['security_pin_verified'] = True
            request.session['security_pin_version'] = str(config.pin_version)
            _clear_pin_attempts(request)
            return redirect(_safe_next_url(request))
        else:
            _record_failed_pin_attempt(request)
            messages.error(request, "Incorrect Security PIN.")
            
    return render(request, 'backup/pin_verify.html')

@login_required
def backup_manager(request):
    if request.user.role != 'doctor':
        messages.error(request, "Access Denied.")
        return redirect('dashboard')

    backup_config = BackupSettings.get_settings()
    if not _is_pin_verified(request, backup_config):
        return _pin_verification_redirect(request)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'update_path':
            new_path = request.POST.get('backup_path', '')
            try:
                backup_dir = _ensure_backup_directory(new_path)
                backup_config.backup_path = str(backup_dir)
                backup_config.save(update_fields=['backup_path'])
                messages.success(request, "Backup path updated.")
            except ValidationError as e:
                messages.error(request, _validation_message(e))
            except OSError:
                messages.error(request, "Unable to create or access the backup directory.")
                
        elif action == 'update_pin':
            new_pin = request.POST.get('new_pin', '')
            try:
                backup_config.set_security_pin(new_pin)
                backup_config.save(update_fields=['security_pin', 'pin_version'])
                request.session['security_pin_version'] = str(backup_config.pin_version)
                messages.success(request, "Security PIN updated successfully.")
            except ValidationError as e:
                messages.error(request, _validation_message(e))

    recent_backups = []
    try:
        backup_dir = _resolve_backup_dir(backup_config.backup_path)
        if backup_dir.exists():
            files = sorted(
                [path for path in backup_dir.iterdir() if path.is_file() and path.suffix == '.sqlite3'],
                key=lambda path: path.stat().st_mtime,
                reverse=True,
            )
            recent_backups = [path.name for path in files[:5]]
    except (ValidationError, OSError):
        recent_backups = []

    return render(request, 'backup/backup_manager.html', {
        'config': backup_config,
        'recent_backups': recent_backups
    })

@login_required
def restore_database(request):
    if request.user.role != 'doctor':
        return redirect('dashboard')

    config = BackupSettings.get_settings()
    if not _is_pin_verified(request, config):
        return _pin_verification_redirect(request)

    if request.method == 'POST':
        backup_file = request.FILES.get('backup_file')
        if not backup_file:
            messages.error(request, "Please choose a backup file to restore.")
            return render(request, 'backup/restore.html')

        if not backup_file.name.lower().endswith('.sqlite3'):
            messages.error(request, "Only .sqlite3 backup files can be restored.")
            return render(request, 'backup/restore.html')

        if backup_file.size > settings.BACKUP_MAX_UPLOAD_SIZE:
            messages.error(request, "Backup file is too large.")
            return render(request, 'backup/restore.html')

        temp_path = None
        try:
            temp_path = _save_uploaded_backup_to_temp(backup_file)
            _validate_sqlite_backup(temp_path)

            db_path = Path(settings.DATABASES['default']['NAME'])
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            before_restore_path = db_path.with_name(f"{db_path.name}.before_restore_{timestamp}")

            connections.close_all()
            shutil.copy2(db_path, before_restore_path)
            os.replace(temp_path, db_path)
            temp_path = None
            connections.close_all()

            auth_logout(request)
            messages.success(request, "Database restored. Please log in again.")
            return redirect('login')
        except ValidationError as e:
            messages.error(request, _validation_message(e))
        except (OSError, sqlite3.DatabaseError):
            messages.error(request, "Restore failed while processing the backup file.")
        finally:
            if temp_path and temp_path.exists():
                temp_path.unlink(missing_ok=True)
    
    return render(request, 'backup/restore.html')
