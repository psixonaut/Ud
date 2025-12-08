from django.contrib import admin
from django.contrib import messages
from django.contrib.auth.models import User, Group
from django.db import IntegrityError, InternalError, transaction
from django.http import HttpResponseRedirect
from .models import Car, Order, Client, Sale, Sale_list, Employee, Test_drive, STATUS_CHOICES



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
            messages.error(request, f"⛔ Ошибка уникальности: Такая запись уже существует.")
        elif "violates not-null constraint" in error_text:
            messages.error(request, f"⛔ Ошибка: Не заполнено обязательное поле.")
        elif "CONTEXT:" in error_text:
            clean_text = error_text.split('CONTEXT:')[0].replace('InternalError:', '').strip()
            clean_text = clean_text.replace('PL/pgSQL function', '').strip()
            if "line" in clean_text: clean_text = clean_text.split('line')[0]
            messages.error(request, f"⛔ {clean_text}")
        else:
            messages.error(request, f"⛔ Ошибка БД: {error_text}")



class SaleListInline(admin.StackedInline):
    model = Sale_list
    extra = 1
    max_num = 1
    min_num = 1
    readonly_fields = ()

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

    class Media:
        js = ('js/admin_auto_price.js',)


    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ('ip_employee', 'passport_client', 'sale_date', 'end_price')
        return ()

    def has_add_permission(self, request):
        return True

    def has_change_permission(self, request, obj=None):
        if obj: return False
        return True

    def has_delete_permission(self, request, obj=None):
        return False



@admin.register(Car)
class CarAdmin(SafeAdminMixin, admin.ModelAdmin):
    list_display = ('vin', 'make', 'model', 'car_status', 'price', 'discount')
    list_filter = ('car_status', 'make')
    search_fields = ('vin', 'model')

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if 'car_status' in form.base_fields:
            field = form.base_fields['car_status']
            if not obj or obj.car_status != 'Продан':
                field.choices = [(k, v) for k, v in STATUS_CHOICES if k != 'Продан']
        return form

    def get_readonly_fields(self, request, obj=None):
        if obj and obj.car_status == 'Продан':
            return [field.name for field in self.model._meta.fields]
        if obj:
            return ('vin', 'make', 'model', 'engine', 'gearbox',
                    'driven_wheels', 'body', 'make_year', 'trim',
                    'addons', 'color', 'date_of_delivery')
        return ()

    def has_delete_permission(self, request, obj=None):
        if obj and obj.car_status == 'Продан': return False
        return super().has_delete_permission(request, obj)



@admin.register(Order)
class OrderAdmin(SafeAdminMixin, admin.ModelAdmin):
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

    def has_change_permission(self, request, obj=None):
        if obj: return False
        return True

    def has_delete_permission(self, request, obj=None): return False


try:
    admin.site.unregister(User)
    admin.site.unregister(Group)
except admin.sites.NotRegistered:
    pass

admin.site.site_header = "Автосалон"
admin.site.index_title = "База данных автосалона"
admin.site.site_title = "Автосалон"