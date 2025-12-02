from django.contrib import admin
# Импортируем все модели из текущего приложения
from .models import Car, Order, Client, Sale, Sale_list, Employee, Test_drive


# ---------------------------------------------------------
# Настройка отображения для модели СОТРУДНИК
# ---------------------------------------------------------
@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    # Что показывать в таблице списка
    list_display = ('id_employee', 'fio', 'rank', 'phone_number', 'employed')

    # По каким полям делать фильтрацию справа
    list_filter = ('rank', 'employed')

    # По каким полям искать (сверху появится строка поиска)
    search_fields = ('fio', 'phone_number', 'passport_employee')


# ---------------------------------------------------------
# Настройка отображения для модели КЛИЕНТ
# ---------------------------------------------------------
@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('passport_client', 'fio', 'phone_number', 'b_day')
    search_fields = ('fio', 'phone_number', 'passport_client', 'license_number')


# ---------------------------------------------------------
# Настройка отображения для модели АВТОМОБИЛЬ
# ---------------------------------------------------------
@admin.register(Car)
class CarAdmin(admin.ModelAdmin):
    list_display = ('vin', 'make', 'model', 'make_year', 'price', 'car_status')
    list_filter = ('car_status', 'make', 'make_year', 'driven_wheels', 'gearbox')
    search_fields = ('vin', 'make', 'model')
    ordering = ('-make_year',)  # Сортировка по году (сначала новые)


# ---------------------------------------------------------
# Настройка отображения для модели ЗАКАЗ
# ---------------------------------------------------------
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id_order', 'state_order', 'date_order', 'make', 'model', 'id_employee')
    list_filter = ('state_order', 'date_order')
    search_fields = ('id_order', 'make', 'model')
    date_hierarchy = 'date_order'  # Удобная навигация по датам сверху


# ---------------------------------------------------------
# Настройка отображения ПРОДАЖИ (с вложенным списком)
# ---------------------------------------------------------

# Сделаем так, чтобы "Состав продажи" (Sale_list) редактировался 
# прямо внутри страницы "Продажи", а не отдельно.
class SaleListInline(admin.TabularInline):
    model = Sale_list
    extra = 0  # Не показывать пустые строки для добавления по умолчанию
    # readonly_fields = (...) # Если нужно запретить редактирование


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ('id_sale', 'sale_date', 'passport_client', 'ip_employee', 'end_price')
    list_filter = ('sale_date',)
    search_fields = ('id_sale',)
    date_hierarchy = 'sale_date'

    # Подключаем вложенную таблицу состава продажи
    inlines = [SaleListInline]


# Отдельно регистрировать Sale_list не обязательно, если он есть внутри Sale,
# но если нужно видеть полный список проданных машин отдельно — можно раскомментировать:
# @admin.register(Sale_list)
# class SaleListAdmin(admin.ModelAdmin):
#     list_display = ('id_sale', 'vin', 'discounted_prise')

# ---------------------------------------------------------
# Настройка отображения для ТЕСТ-ДРАЙВА
# ---------------------------------------------------------
@admin.register(Test_drive)
class TestDriveAdmin(admin.ModelAdmin):
    list_display = ('id_test', 'datetime_reservation', 'passport_client', 'vin', 'result')
    list_filter = ('result', 'datetime_reservation')
    search_fields = ('passport_client__fio', 'vin__vin')  # Поиск по полям связанных таблиц