from django.contrib import admin
from django.contrib import messages
from django.db import IntegrityError, InternalError, transaction, DatabaseError
from .models import Car, Order, Client, Sale, Sale_list, Employee, Test_drive


# --- ЛОВУШКА ОШИБОК (Mixin) ---
class SafeAdminMixin:
    """
    Перехватывает любые ошибки базы данных, не давая сайту упасть (Error 500).
    Выводит ошибку как красное уведомление.
    """

    def save_model(self, request, obj, form, change):
        try:
            # transaction.atomic() обязателен! Без него ошибка БД ломает соединение
            # и вызывает TransactionManagementError
            with transaction.atomic():
                super().save_model(request, obj, form, change)
        except Exception as e:
            self.handle_db_error(request, e)

    def delete_model(self, request, obj):
        try:
            with transaction.atomic():
                super().delete_model(request, obj)
        except Exception as e:
            self.handle_db_error(request, e)

    def handle_db_error(self, request, exception):
        """
        Разбирает текст ошибки и делает его понятным для человека.
        """
        error_text = str(exception)

        # 1. Ошибка дубликатов (Сбился счетчик ID или уникальное поле)
        if "duplicate key value" in error_text:
            messages.error(request,
                           f"⛔ Ошибка уникальности: Запись с таким ID или номером уже существует. (Возможно, сбился счетчик БД, попробуйте создать запись еще раз).")

        # 2. Ошибка пустых полей (NOT NULL)
        elif "violates not-null constraint" in error_text:
            messages.error(request, f"⛔ Ошибка: Не заполнено обязательное поле. Проверьте форму.")

        # 3. Ошибки бизнес-логики (Триггеры)
        elif "CONTEXT:" in error_text:
            # Очищаем технический текст PostgreSQL
            clean_text = error_text.split('CONTEXT:')[0].replace('InternalError:', '').strip()
            messages.error(request, f"⛔ {clean_text}")

        # 4. Прочие ошибки
        else:
            messages.error(request, f"⛔ Системная ошибка базы данных: {error_text}")


# --- Настройки моделей ---

class SaleListInline(admin.StackedInline):
    model = Sale_list
    extra = 0
    readonly_fields = ('vin', 'discounted_prise')

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Sale)
class SaleAdmin(SafeAdminMixin, admin.ModelAdmin):
    list_display = ('id_sale', 'sale_date', 'ip_employee', 'end_price')
    inlines = [SaleListInline]

    def has_change_permission(self, request, obj=None):
        return not bool(obj)

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Car)
class CarAdmin(SafeAdminMixin, admin.ModelAdmin):
    list_display = ('vin', 'make', 'model', 'car_status', 'price', 'discount')
    list_filter = ('car_status', 'make')
    search_fields = ('vin', 'model')

    def get_readonly_fields(self, request, obj=None):
        if obj and obj.car_status == 'Продан':
            # Блокируем всё, если продана
            return [field.name for field in self.model._meta.fields]
        if obj:
            # Блокируем тех. данные при редактировании
            return ('vin', 'make', 'model', 'engine', 'gearbox',
                    'driven_wheels', 'body', 'make_year', 'trim',
                    'addons', 'color', 'date_of_delivery')
        return ()

    def has_delete_permission(self, request, obj=None):
        if obj and obj.car_status == 'Продан':
            return False
        return super().has_delete_permission(request, obj)


@admin.register(Order)
class OrderAdmin(SafeAdminMixin, admin.ModelAdmin):
    list_display = ('id_order', 'make', 'model', 'state_order')


@admin.register(Client)
class ClientAdmin(SafeAdminMixin, admin.ModelAdmin):
    list_display = ('fio', 'phone_number', 'license_number')


@admin.register(Employee)
class EmployeeAdmin(SafeAdminMixin, admin.ModelAdmin):
    list_display = ('fio', 'rank', 'phone_number')


@admin.register(Test_drive)
class TestDriveAdmin(SafeAdminMixin, admin.ModelAdmin):
    list_display = ('id_test', 'datetime_reservation', 'vin', 'id_employee')
    list_filter = ('datetime_reservation', 'result')

    def has_change_permission(self, request, obj=None):
        return not bool(obj)

    def has_delete_permission(self, request, obj=None):
        return False