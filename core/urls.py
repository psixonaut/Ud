from django.urls import path
from . import views

urlpatterns = [
    path('', views.custom_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),

    path('cars/', views.car_list, name='car_list'),

    path('orders/', views.order_list, name='order_list'),
    path('orders/new/', views.create_order, name='create_order'),
    path('orders/<int:order_id>/accept/', views.accept_car, name='accept_car'),

    path('sales/new/', views.create_sale, name='create_sale'),

    path('test-drives/', views.test_drive_list, name='test_drive_list'),
    path('test-drives/new/', views.create_test_drive, name='create_test_drive'),

    path('employees/', views.employee_list, name='employee_list'),
    path('employees/<int:emp_id>/fire/', views.fire_employee, name='fire_employee'),
]