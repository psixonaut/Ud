from django.contrib import admin
from django.contrib import messages
from django.contrib.auth.models import User, Group
from django.db import IntegrityError, InternalError, transaction
from django.http import HttpResponseRedirect
from .models import Car, Order, Client, Sale, Sale_list, Employee, Test_drive, STATUS_CHOICES


# --- 1. ЛОВУШКА ОШИБОК (Mixin) ---
class SafeAdminMixin:
    """
    Этот класс перехватывает ошибки от базы данных (триггеры, ограничения)
    и выводит их как красное уведомление, перезагружая страницу.
    """

    def changeform_view(self, request, object_id=None, form_url='', extra_context=None):
        try:
            # Оборачиваем всё действие в транзакцию. Если ошибка - откат.
            with transaction.atomic():
                return super().changeform_view(request, object_id, form_url, extra_context)
        except Exception as e:
            self.handle_db_error(request, e)
            # Перезагружаем страницу, чтобы сбросить форму
            return HttpResponseRedirect(request.path)

    def delete_view(self, request, object_id, extra_context=None):
        try:
            with transaction.atomic():
                return super().delete_view(request, object_id, extra_context)
        except Exception as e:
            self.handle_db_error(request, e)
            return HttpResponseRedirect(request.path)

    def handle_db_error(self, request, exception):
        """Парсинг текста ошибки от PostgreSQL"""
        error_text = str(exception)

        if "duplicate key value" in error_text:
            messages.error(request, f"⛔ Ошибка уникальности: Такая запись уже существует (или сбился счетчик ID).")
        elif "violates not-null constraint" in error_text:
            messages.error(request, f"⛔ Ошибка: Не заполнено обязательное поле.")
        elif "CONTEXT:" in error_text:
            # Очищаем текст ошибки от технического мусора
            clean_text = error_text.split('CONTEXT:')[0].replace('InternalError:', '').strip()
            clean_text = clean_text.replace('PL/pgSQL function', '').strip()
            # Убираем название функции триггера, если оно попало в текст
            if "line" in clean_text:
                clean_text = clean_text.split('line')[0]
            messages.error(request, f"⛔ {clean_text}")
        else:
            messages.error(request, f"⛔ Ошибка БД: {error_text}")


# --- 2. НАСТРОЙКИ ПРОДАЖИ ---

class SaleListInline(admin.StackedInline):
    model = Sale_list
    extra = 1
    # Поле цены доступно для редактирования (чтобы можно было ввести свою сумму)
    readonly_fields = ()

    # Запрещаем удалять/менять строки, если продажа уже проведена
    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        if obj: return False
        return True

    def has_add_permission(self, request, obj=None):
        if obj: return False
        return True


@admin.register(Sale)
class SaleAdmin(SafeAdminMixin, admin.ModelAdmin):
    list_display = ('id_sale', 'sale_date', 'ip_employee', 'end_price')
    inlines = [SaleListInline]
    # Итоговую цену в "шапке" блокируем (она считается сама)
    readonly_fields = ('end_price',)

    # Можно создавать новые
    def has_add_permission(self, request): return True

    # Нельзя менять старые
    def has_change_permission(self, request, obj=None):
        if obj: return False
        return True

    # Нельзя удалять
    def has_delete_permission(self, request, obj=None): return False


# --- 3. НАСТРОЙКИ АВТОМОБИЛЯ ---

@admin.register(Car)
class CarAdmin(SafeAdminMixin, admin.ModelAdmin):
    list_display = ('vin', 'make', 'model', 'car_status', 'price', 'discount')
    list_filter = ('car_status', 'make')
    search_fields = ('vin', 'model')

    def get_form(self, request, obj=None, **kwargs):
        """Убираем статус 'Продан' из выпадающего списка при редактировании"""
        form = super().get_form(request, obj, **kwargs)

        # --- ИСПРАВЛЕНИЕ ЗДЕСЬ ---
        # Проверяем, существует ли поле 'car_status' в форме.
        # Если машина уже продана, поле становится read-only и исчезает из form.base_fields.
        if 'car_status' in form.base_fields:
            field = form.base_fields['car_status']
            # Если это новая машина или старая, но еще не проданная
            if not obj or obj.car_status != 'Продан':
                # Оставляем все статусы КРОМЕ 'Продан'
                field.choices = [(k, v) for k, v in STATUS_CHOICES if k != 'Продан']

        return form

    def get_readonly_fields(self, request, obj=None):
        """
        Логика:
        1. Если 'Продан' -> Блокируем ВСЁ (история не меняется).
        2. Если 'В продаже' -> Разрешаем менять всё (чтобы исправить опечатки).
        """
        # Если машина продана - блокируем всё (это правило должно остаться)
        if obj and obj.car_status == 'Продан':
            return [field.name for field in self.model._meta.fields]

        # В остальных случаях - ничего не блокируем, можно править всё
        return ()

    def has_delete_permission(self, request, obj=None):
        # Запрещаем удалять проданные машины (история)
        if obj and obj.car_status == 'Продан': return False
        return super().has_delete_permission(request, obj)


# --- 4. ОСТАЛЬНЫЕ МОДЕЛИ ---

@admin.register(Order)
class OrderAdmin(SafeAdminMixin, admin.ModelAdmin):
    # Убрали id_order, добавили полезные поля
    list_display = ('make', 'model', 'state_order', 'date_order', 'amount')
    list_filter = ('state_order', 'date_order')


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

    # Запрещаем менять прошедшие тест-драйвы
    def has_change_permission(self, request, obj=None):
        if obj: return False
        return True

    def has_delete_permission(self, request, obj=None): return False


# --- 5. ЧИСТКА ИНТЕРФЕЙСА (Убираем Users/Groups) ---
try:
    admin.site.unregister(User)
    admin.site.unregister(Group)
except admin.sites.NotRegistered:
    pass