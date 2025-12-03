from django.contrib import admin
from django.urls import path
from django.views.generic import RedirectView
from core.api import api

urlpatterns = [
    # Перенаправление с главной страницы сразу в админку
    path('', RedirectView.as_view(url='/admin/')),

    path('admin/', admin.site.urls),
    path('api/', api.urls),
]