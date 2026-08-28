from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from datetime import date
from django.db.models import Q
from django.contrib.staticfiles import finders
from django.http import HttpResponse, JsonResponse  # <--- CRITICAL FIX: Added JsonResponse
from django.conf import settings
import base64
from functools import wraps

from django.db import IntegrityError

# --- MODELS & UTILS ---
from .models import Client, Login, SiteSetting, SoftwareUpdate # <--- Added SoftwareUpdate
from .utils import generate_license, calculate_expiry_date
from .scratch_renderer import get_scratch_card_html 

# ==========================================
# 1. AUTHENTICATION & DECORATORS
# ==========================================
# licenses/views.py

def register(request):
    # If already logged in, send to dashboard
    if request.session.get('is_master_admin'):
        return redirect('dashboard')

    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        special_code = request.POST.get('special_code')

        # --- SECURITY SETTING ---
        # Only users who know this code can register
        SECRET_CODE = "BARFNU" 

        if special_code != SECRET_CODE:
            messages.error(request, "Invalid Special Code! You are not authorized to register.")
            return redirect('register')

        # Check if username exists
        if Login.objects.filter(username=username).exists():
            messages.error(request, "Username already taken.")
            return redirect('register')

        try:
            # Create new admin user
            new_user = Login(username=username)
            new_user.set_password(password) # This handles the hashing automatically
            new_user.save()
            
            messages.success(request, "Account created successfully! Please login.")
            return redirect('login')
            
        except Exception as e:
            messages.error(request, f"Registration failed: {str(e)}")
            return redirect('register')

    return render(request, 'register.html')

def admin_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.session.get('is_master_admin'):
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def login_view(request):
    if request.session.get('is_master_admin'):
        return redirect('dashboard')

    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        remember_me = request.POST.get('remember_me')
        
        try:
            user = Login.objects.get(username=username)
            if user.check_password(password):
                # Set session data
                request.session['is_master_admin'] = True
                request.session['admin_username'] = user.username
                
                # Handle Remember Me
                if remember_me:
                    request.session.set_expiry(2592000)  # 30 days
                else:
                    request.session.set_expiry(86400)  # 24 hours
                
                return redirect(request.GET.get('next', 'dashboard'))
            else:
                messages.error(request, "Incorrect Password")
        except Login.DoesNotExist:
            messages.error(request, "User not found")
    return render(request, 'login.html')

def logout_view(request):
    request.session.flush()
    return redirect('login')

# ==========================================
# 2. CLIENT MANAGEMENT (DASHBOARD)
# ==========================================

@admin_required
def dashboard(request):
    # Handle Key Generation
    if request.method == 'POST':
        name = request.POST.get('name')
        hw_id = request.POST.get('hardware_id')
        duration_val = request.POST.get('duration')
        action_type = request.POST.get('action_type')
        
        if name and hw_id and duration_val:
            try:
                days = int(duration_val)
                duration_seconds = days * 24 * 60 * 60
                
                secret_key = generate_license(hw_id, duration_seconds)
                
                new_client = Client.objects.create(
                    name=name, hardware_id=hw_id, secret_key=secret_key,
                    validity_seconds=int(duration_seconds), created_at=timezone.now()
                )

                if action_type == 'download_scratch':
                    return download_card(request, new_client.id)

                request.session['generated_new_key'] = {
                    'key': secret_key,
                    'expiry': new_client.expiry_date.strftime("%d %b %Y")
                }
                messages.success(request, f"License generated for {name}!")
                return redirect('dashboard')
            except IntegrityError:
                messages.error(request, "Error: A license for this Hardware ID already exists.")
                return redirect('dashboard')
            except Exception as e:
                messages.error(request, f"Error: {e}")
                return redirect('dashboard')
        else:
            messages.error(request, "Please fill in all fields.")
            return redirect('dashboard')

    # Display Data
    generated_key_data = request.session.pop('generated_new_key', None)
    generated_key = None
    expiry_date_str = None
    
    if generated_key_data:
        generated_key = generated_key_data['key']
        expiry_date_str = generated_key_data['expiry']

    query = request.GET.get('q')
    if query:
        clients = Client.objects.filter(Q(name__icontains=query) | Q(hardware_id__icontains=query)).order_by('-created_at')
    else:
        clients = Client.objects.all().order_by('-created_at')

    active_count = sum(1 for c in Client.objects.all() if c.is_active)

    site_settings = SiteSetting.load()
    github_warning = None
    if site_settings.github_token_expiry:
        days_left = (site_settings.github_token_expiry - date.today()).days
        if days_left <= 7:
            github_warning = f"GitHub token expires in {days_left} days! Renew it in Settings."

    return render(request, 'dashboard.html', {
        'clients': clients,
        'active_count': active_count,
        'generated_key': generated_key,
        'expiry_date': expiry_date_str,
        'github_warning': github_warning,
    })

@admin_required
def delete_client(request, client_id):
    client = get_object_or_404(Client, id=client_id)
    name = client.name
    client.delete()
    messages.success(request, f"Client '{name}' deleted successfully.")
    return redirect('dashboard')

@admin_required
def download_card(request, client_id):
    client = get_object_or_404(Client, id=client_id)
    
    logo_base64 = None
    try:
        # Use logo from settings if available, else default
        logo_path = None
        if hasattr(settings, 'BRANDING'):
             logo_path = finders.find(settings.BRANDING['LOGO_PATH'])
        else:
             logo_path = finders.find('images/billofy_key.png')

        if logo_path:
            with open(logo_path, "rb") as image_file:
                logo_base64 = base64.b64encode(image_file.read()).decode('utf-8')
    except Exception as e:
        print(f"Logo error: {e}") 

    html_content = get_scratch_card_html(
        client.secret_key, 
        client.hardware_id, 
        client.expiry_date.strftime("%d %b %Y"),
        logo_base64 
    )
    
    response = HttpResponse(html_content, content_type='text/html')
    filename = f"License_{client.hardware_id[:6]}.html"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response

# ==========================================
# 3. SITE SETTINGS & HOME
# ==========================================

@admin_required
def home_view(request):
    """Home page with dashboard overview"""
    clients = Client.objects.all().order_by('-created_at')
    total_clients = clients.count()
    active_count = sum(1 for c in clients if c.is_active)
    expired_count = total_clients - active_count
    recent_clients = clients[:5]
    
    site_settings = SiteSetting.load()
    github_warning = None
    if site_settings.github_token_expiry:
        days_left = (site_settings.github_token_expiry - date.today()).days
        if days_left <= 7:
            github_warning = f"GitHub token expires in {days_left} days! Renew it in Settings."

    return render(request, 'home.html', {
        'total_clients': total_clients,
        'active_count': active_count,
        'expired_count': expired_count,
        'recent_clients': recent_clients,
        'github_warning': github_warning,
    })

@admin_required
def settings_view(request):
    site_settings = SiteSetting.load()
    
    if request.method == 'POST':
        site_settings.project_name = request.POST.get('project_name', '').strip()
        site_settings.project_name_short = request.POST.get('project_name_short', '').strip()
        site_settings.primary_color = request.POST.get('primary_color', '').strip()
        
        # 🚀 NAYA: GitHub fields — sirf tab update karo jab naya token diya ho
        new_token = request.POST.get('github_token', '').strip()
        if new_token:
            site_settings.github_token = new_token
        
        github_repo = request.POST.get('github_repo', '').strip()
        if github_repo:
            site_settings.github_repo = github_repo
        
        expiry = request.POST.get('github_token_expiry')
        if expiry:
            site_settings.github_token_expiry = expiry
        
        if 'logo' in request.FILES:
            site_settings.logo = request.FILES['logo']
        
        if site_settings.project_name:
            site_settings.save()
            messages.success(request, "Settings updated successfully!")
            return redirect('settings')
        else:
            messages.error(request, "Project name is required.")
    
    return render(request, 'settings.html', {'settings': site_settings})



# ==========================================
# 4. UPDATE SYSTEM (SERVER SIDE)
# ==========================================
# Upar imports me ye add karo
from .github_release import push_to_github
import os
from django.conf import settings

@admin_required
def push_update_view(request):
    """
    Handles uploading new update files (EXE) to the database AND pushing to GitHub Releases.
    """
    clients = Client.objects.all().order_by('-created_at')
    active_count = sum(1 for c in clients if c.is_active)
    
    if request.method == 'POST':
        version = request.POST.get('version', '').strip()
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        update_type = request.POST.get('update_type', 'optional')
        
        if 'update_file' in request.FILES and version and title:
            # --- YAHAN NAYI CHECK ADD KARO ---
            if SoftwareUpdate.objects.filter(version=version).exists():
                messages.error(request, f"Update version v{version} already exists! Please use a different version or delete the old one first.")
                return redirect('push_update')
            # ---------------------------------
            
            try:
                # 1. Pehle local DB me save karo (taaki file physically system me aa jaye)
                update_obj = SoftwareUpdate.objects.create(
                    version=version,
                    title=title,
                    description=description,
                    update_file=request.FILES['update_file'],
                    update_type=update_type,
                    is_active=True
                )
                
                
                # 2. File ka actual path nikalo
                file_path = update_obj.update_file.path
                
                # 3. GitHub par push karo (API call)
                is_success, gh_result = push_to_github(version, title, description, file_path)
                
                if is_success:
                    # Agar success hua toh GitHub ka real download URL DB me save kar do
                    update_obj.download_url = gh_result
                    update_obj.save()
                    messages.success(request, f"Update v{version} pushed to GitHub successfully!")
                else:
                    # Agar fail hua toh user ko batao
                    messages.warning(request, f"Saved locally, BUT GitHub push failed: {gh_result}")
                    
                return redirect('push_update')
                
            except Exception as e:
                messages.error(request, f"Error saving update: {str(e)}")
        else:
            messages.error(request, "Version, Title, and File are required.")
            
    return render(request, 'push_update.html', {
        'clients': clients,
        'active_count': active_count,
    })

# ---------------------------------------------------------
# 2. UPDATE LIST VIEW (New)
# ---------------------------------------------------------
@admin_required
def update_list_view(request):
    """
    Displays the full history of updates.
    """
    # Fetch all updates, newest first
    updates = SoftwareUpdate.objects.all().order_by('-created_at')
    
    return render(request, 'update_list.html', {
        'updates': updates,
    })


# ---------------------------------------------------------
# 3. DELETE UPDATES VIEW (New)
# ---------------------------------------------------------
@admin_required
def delete_updates_view(request):
    """
    Handles deleting updates (Single button or Bulk checkboxes).
    """
    if request.method == 'POST':
        # 1. Check for Single Delete (Trash icon click)
        single_delete_id = request.POST.get('delete_single')
        
        if single_delete_id:
            try:
                update = get_object_or_404(SoftwareUpdate, id=single_delete_id)
                v_num = update.version
                update.delete()
                messages.success(request, f"Update v{v_num} deleted successfully.")
            except Exception as e:
                messages.error(request, f"Error deleting update: {str(e)}")

        # 2. Check for Bulk Delete (Select All -> Delete Selected)
        else:
            update_ids = request.POST.getlist('update_ids') # Returns list of IDs
            
            if update_ids:
                try:
                    # Filter and delete
                    updates_to_delete = SoftwareUpdate.objects.filter(id__in=update_ids)
                    count = updates_to_delete.count()
                    updates_to_delete.delete()
                    messages.success(request, f"Successfully deleted {count} updates.")
                except Exception as e:
                    messages.error(request, f"Error deleting updates: {str(e)}")
            else:
                messages.warning(request, "No updates selected for deletion.")
    
    return redirect('update_list')

# ==========================================
# 5. UPDATE SYSTEM (CLIENT SIDE)
# ==========================================

def check_update_api(request):
    """
    The Billing App calls this URL to check if a new version exists.
    Returns JSON data about the latest active update.
    """
    # Get the latest active update from DB
    latest = SoftwareUpdate.objects.filter(is_active=True).order_by('-created_at').first()
    
    if latest:
        return JsonResponse({
            'version': latest.version,
            'title': latest.title,
            'notes': latest.description,
            # This generates the full URL (e.g. http://127.0.0.1:8700/media/updates/file.exe)
            'download_url': request.build_absolute_uri(latest.update_file.url),
            'date': latest.created_at.strftime("%Y-%m-%d")
        })
    
    # No active updates found
    return JsonResponse({'version': '0.0.0'})