"""
URL configuration for key_generation project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from licenses.views import *

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', login_view, name='login'),
    path('home/', home_view, name='home'),
    path('register/', register, name='register'),
    path('dashboard/', dashboard, name='dashboard'),
    path('push-update/', push_update_view, name='push_update'),
    path('logout/', logout_view, name='logout'),
    path('delete/<int:client_id>/', delete_client, name='delete_client'),
    path('download-card/<int:client_id>/', download_card, name='download_card'),
    path('settings/', settings_view, name='settings'),


    # Update System URLs
    path('push-update/', push_update_view, name='push_update'),
    path('updates/list/', update_list_view, name='update_list'),
    path('updates/delete/', delete_updates_view, name='delete_updates'),
    path('api/check-update/', check_update_api, name='check_update_api'), # API URL
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)