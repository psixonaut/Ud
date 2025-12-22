from django.urls import path
from . import views

urlpatterns = [
    # АВТОРИЗАЦИЯ
    path('', views.custom_login, name='login'),
    path('logout/', views.user_logout, name='logout'),

    # ГЛАВНАЯ
    path('dashboard/', views.dashboard, name='dashboard'),

    # АВТОМОБИЛИ
    path('cars/', views.car_list, name='car_list'),
    path('cars/<str:vin>/', views.car_detail, name='car_detail'),
    path('cars/<str:vin>/edit/', views.edit_car, name='edit_car'),

    # ЗАКУПКИ
    path('orders/', views.order_list, name='order_list'),
    path('orders/new/', views.create_order, name='create_order'),
    path('orders/<int:order_id>/accept/', views.accept_car, name='accept_car'),
    path('orders/<int:order_id>/', views.order_detail, name='order_detail'),

    # ПРОДАЖИ
    path('sales/', views.sale_list, name='sale_list'),
    path('sales/new/', views.create_sale, name='create_sale'),
    path('sales/<int:sale_id>/', views.sale_detail, name='sale_detail'),

    # ТЕСТ-ДРАЙВЫ
    path('test-drives/', views.test_drive_list, name='test_drive_list'),
    path('test-drives/new/', views.create_test_drive, name='create_test_drive'),
    path('test-drives/<int:td_id>/', views.test_drive_detail, name='test_drive_detail'),
    path('test-drives/<int:td_id>/edit/', views.edit_test_drive, name='edit_test_drive'),

    # ПЕРСОНАЛ
    path('employees/', views.employee_list, name='employee_list'),
    path('employees/new/', views.add_employee, name='add_employee'),
    path('employees/<int:emp_id>/fire/', views.fire_employee, name='fire_employee'),
    path('employees/<int:emp_id>/edit/', views.edit_employee, name='edit_employee'),

    # КЛИЕНТЫ
    path('clients/', views.client_list, name='client_list'),
    path('clients/new/', views.add_client, name='add_client'),
    path('clients/<int:passport_id>/delete/', views.delete_client, name='delete_client'),
]