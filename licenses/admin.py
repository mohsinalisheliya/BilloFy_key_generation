from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import *
# Register your models here.
admin.site.site_header = admin.site.site_title = "Key Generation"

all_models = [
   Client,
   Login,
   SoftwareUpdate,
   SiteSetting,
   


]

for model in all_models:
    admin.site.register(model)