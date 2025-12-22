from django.contrib import admin
from django.urls import path, include
from core.api import api

urlpatterns = [
    path('api/', api.urls),
    path('', include('core.urls')),
]