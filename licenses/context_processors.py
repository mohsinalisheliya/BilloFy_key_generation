from django.conf import settings
from .models import SiteSetting

def branding(request):
    """
    Context processor to make branding configuration available to all templates.
    Reads from database (SiteSetting model) with fallback to settings.py.
    This allows templates to access {{ BRANDING.PROJECT_NAME }}, {{ BRANDING.LOGO_PATH }}, etc.
    """
    try:
        # Load from database
        site_settings = SiteSetting.load()
        return {
            'BRANDING': {
                'PROJECT_NAME': site_settings.project_name,
                'PROJECT_NAME_SHORT': site_settings.project_name_short,
                'LOGO_PATH': site_settings.get_logo_url(),  # Use method to get correct URL
                'PRIMARY_COLOR': site_settings.primary_color,
            }
        }
    except Exception as e:
        # Fallback to settings.py if database not available
        print(f"Branding context processor error: {e}")
        return {
            'BRANDING': settings.BRANDING
        }
