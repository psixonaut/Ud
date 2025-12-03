from django.contrib import admin
from .models import Car, Order, Client, Sale, Sale_list, Employee, Test_drive


class SaleListInline(admin.StackedInline):
    model = Sale_list
    extra = 0
    # Блокируем редактирование цены в составе, она считается автоматически
    readonly_fields = ('discounted_prise',)


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ('id_sale', 'sale_date', 'ip_employee', 'end_price')
    inlines = [SaleListInline]

    # Правило: С продажами автомобилей нельзя производить никаких изменений
    # (Запрещаем удаление и изменение самой записи продажи, если она уже создана)
    def has_change_permission(self, request, obj=None):
        if obj:  # Если объект уже существует
            return False
        return True  # Создавать новые можно


@admin.register(Car)
class CarAdmin(admin.ModelAdmin):
    list_display = ('vin', 'make', 'model', 'car_status', 'price', 'discount')
    list_filter = ('car_status', 'make')
    search_fields = ('vin', 'model')

    # Правило: У автомобиля можно изменить только цену, статус и скидку
    # Все остальные поля делаем readonly при редактировании
    def get_readonly_fields(self, request, obj=None):
        if obj:  # Если редактируем существующий авто
            return ('vin', 'make', 'model', 'engine', 'gearbox',
                    'driven_wheels', 'body', 'make_year', 'trim',
                    'addons', 'color', 'date_of_delivery')
        return ()


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('fio', 'rank', 'phone_number')


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('fio', 'phone_number', 'license_number')


@admin.register(Test_drive)
class TestDriveAdmin(admin.ModelAdmin):
    list_display = ('id_test', 'datetime_reservation', 'vin', 'id_employee')
    list_filter = ('datetime_reservation', 'id_employee')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id_order', 'make', 'model', 'state_order', 'amount')