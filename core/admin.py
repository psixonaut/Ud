from django.contrib import admin
from .models import Car, Order, Client, Sale, Sale_list, Employee, Test_drive


# --- Миксин для запрета редактирования ---
class ReadOnlyAdminMixin:
    """
    Запрещает редактирование и удаление уже созданных записей.
    """

    def has_change_permission(self, request, obj=None):
        # Если открыли конкретную запись (obj не None) -> запрещаем
        if obj:
            return False
        # Если просто смотрим список -> разрешаем
        return True

    def has_delete_permission(self, request, obj=None):
        # Запрещаем удаление
        return False


# --- Продажа ---

class SaleListInline(admin.StackedInline):
    model = Sale_list
    extra = 0
    # Поля только для чтения
    readonly_fields = ('vin', 'discounted_prise')

    # Нельзя удалять вложенные элементы из старых продаж
    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Sale)
class SaleAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = ('id_sale', 'sale_date', 'ip_employee', 'end_price')
    inlines = [SaleListInline]
    # Все поля делаем серыми (неактивными)
    readonly_fields = ('ip_employee', 'passport_client', 'sale_date', 'end_price')


# --- Тест-драйв ---

@admin.register(Test_drive)
class TestDriveAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = ('id_test', 'datetime_reservation', 'vin', 'id_employee', 'result')
    list_filter = ('datetime_reservation', 'result')
    readonly_fields = ('vin', 'passport_client', 'id_employee', 'datetime_reservation', 'result')


# --- Остальные модели ---

@admin.register(Car)
class CarAdmin(admin.ModelAdmin):
    list_display = ('vin', 'make', 'model', 'car_status', 'price', 'discount')
    list_filter = ('car_status', 'make')
    search_fields = ('vin', 'model')

    def get_readonly_fields(self, request, obj=None):
        """
        Логика блокировки полей:
        1. Если машина 'Продан' -> Блокируем ВСЕ поля.
        2. Если машина в другом статусе -> Блокируем только технические хар-ки (разрешаем менять цену/статус).
        3. Если создаем новую -> Ничего не блокируем.
        """
        # Сценарий 1: Машина уже продана
        if obj and obj.car_status == 'Продан':
            # Получаем список вообще всех полей модели и делаем их read-only
            return [field.name for field in self.model._meta.fields]

        # Сценарий 2: Редактируем непроданную машину (блокируем неизменяемые тех. данные)
        if obj:
            return ('vin', 'make', 'model', 'engine', 'gearbox',
                    'driven_wheels', 'body', 'make_year', 'trim',
                    'addons', 'color', 'date_of_delivery')

        # Сценарий 3: Создание новой машины (всё открыто)
        return ()

    def has_delete_permission(self, request, obj=None):
        """
        Запрещаем удалять машину, если она уже продана (для сохранения истории).
        """
        if obj and obj.car_status == 'Продан':
            return False
        return super().has_delete_permission(request, obj)

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('fio', 'rank', 'phone_number')


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('fio', 'phone_number', 'license_number')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id_order', 'make', 'model', 'state_order')