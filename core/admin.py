from django.contrib import admin
from django.contrib import messages
from django.db import IntegrityError, InternalError, transaction
from django.http import HttpResponseRedirect
from .models import Car, Order, Client, Sale, Sale_list, Employee, Test_drive


class SafeAdminMixin:
    def changeform_view(self, request, object_id=None, form_url='', extra_context=None):
        try:
            with transaction.atomic():
                return super().changeform_view(request, object_id, form_url, extra_context)
        except Exception as e:
            self.handle_db_error(request, e)
            return HttpResponseRedirect(request.path)

    def delete_view(self, request, object_id, extra_context=None):
        try:
            with transaction.atomic():
                return super().delete_view(request, object_id, extra_context)
        except Exception as e:
            self.handle_db_error(request, e)
            return HttpResponseRedirect(request.path)

    def handle_db_error(self, request, exception):
        error_text = str(exception)
        if "duplicate key value" in error_text:
            messages.error(request, f"⛔ Ошибка уникальности: Такая запись уже существует (ID/Паспорт/ВУ/VIN).")
        elif "violates not-null constraint" in error_text:
            messages.error(request, f"⛔ Ошибка: Не заполнено обязательное поле.")
        elif "CONTEXT:" in error_text:
            clean_text = error_text.split('CONTEXT:')[0].replace('InternalError:', '').strip()
            clean_text = clean_text.replace('PL/pgSQL function', '').strip()
            messages.error(request, f"⛔ {clean_text}")
        else:
            messages.error(request, f"⛔ Ошибка БД: {error_text}")


class SaleListInline(admin.StackedInline):
    model = Sale_list
    extra = 0
    readonly_fields = ('vin', 'discounted_prise')
    can_delete = False


@admin.register(Sale)
class SaleAdmin(SafeAdminMixin, admin.ModelAdmin):
    list_display = ('id_sale', 'sale_date', 'ip_employee', 'end_price')
    inlines = [SaleListInline]
    readonly_fields = ('ip_employee', 'passport_client', 'sale_date', 'end_price')

    def has_change_permission(self, request, obj=None):
        return not bool(obj)  # Разрешить создание, запретить редактирование

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Car)
class CarAdmin(SafeAdminMixin, admin.ModelAdmin):
    list_display = ('vin', 'make', 'model', 'car_status', 'price', 'discount')
    list_filter = ('car_status', 'make')
    search_fields = ('vin', 'model')

    def get_readonly_fields(self, request, obj=None):
        if obj and obj.car_status == 'Продан':
            return [field.name for field in self.model._meta.fields]
        if obj:
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