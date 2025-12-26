from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q
from .models import Client
from .utils import generate_license

# --- LOGIN VIEW ---
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages

def login_view(request):
    # If user is already logged in, send them to dashboard immediately
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            
            user = authenticate(username=username, password=password)
            
            if user is not None:
                login(request, user)
                # Redirect to 'next' if it exists (e.g. they tried accessing a protected page)
                next_url = request.GET.get('next', 'dashboard')
                return redirect(next_url)
            else:
                messages.error(request, "Invalid username or password.")
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()

    return render(request, 'login.html', {'form': form})

# --- LOGOUT VIEW ---
def logout_view(request):
    logout(request)
    return redirect('login')

# --- DELETE VIEW ---
@login_required(login_url='login')
def delete_client(request, client_id):
    client = get_object_or_404(Client, id=client_id)
    client.delete()
    messages.success(request, "Client deleted successfully.")
    return redirect('dashboard')

# --- DASHBOARD VIEW ---
@login_required(login_url='login') 
def dashboard(request):
    
    # 1. HANDLE KEY GENERATION
    if request.method == 'POST':
        name = request.POST.get('name')
        hw_id = request.POST.get('hw_id')
        duration_val = request.POST.get('days') 
        
        if name and hw_id and duration_val:
            try:
                secret_key = generate_license(hw_id, duration_val)
                
                Client.objects.create(
                    name=name,
                    hardware_id=hw_id,
                    secret_key=secret_key,
                    validity_seconds=int(duration_val),
                    created_at=timezone.now()
                )
                messages.success(request, f"License generated for {name}!")
            except Exception as e:
                messages.error(request, f"Error: {e}")
        else:
            messages.error(request, "Please fill in all fields.")
            
        return redirect('dashboard')
            
    # 2. HANDLE LIST & SEARCH
    query = request.GET.get('q')
    if query:
        clients = Client.objects.filter(
            Q(name__icontains=query) | Q(hardware_id__icontains=query)
        ).order_by('-created_at')
    else:
        clients = Client.objects.all().order_by('-created_at')

    # Calculate active count based on the property
    active_count = sum(1 for c in Client.objects.all() if c.is_active)

    context = {
        'clients': clients,
        'active_count': active_count
    }
    return render(request, 'dashboard.html', context)