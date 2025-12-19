from django.contrib import admin
from django.urls import path, include
from core.api import api

urlpatterns = [
    # Админка Django (для разработчика)
    path('admin/', admin.site.urls),

    # API (нужно для авто-подстановки цены в админке)
    path('api/', api.urls),

    # Подключение всех путей из core/urls.py
    path('', include('core.urls')),
]