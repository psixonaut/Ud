from ninja import NinjaAPI, ModelSchema
from ninja.pagination import paginate
from typing import List, Optional
from django.shortcuts import get_object_or_404
# Импортируем твои модели
from .models import Car, Order, Client, Sale, Employee, Test_drive

# Создаем экземпляр API
api = NinjaAPI(title="Car Dealer API")

# ==========================================
# 1. СХЕМЫ (SCHEMAS)
# Описываем, как данные будут выглядеть в JSON
# ==========================================

class CarSchema(ModelSchema):
    class Meta:
        model = Car
        # Можно перечислить конкретные поля или взять все ("__all__")
        fields = "__all__"

class ClientSchema(ModelSchema):
    class Meta:
        model = Client
        fields = ['passport_client', 'fio', 'phone_number', 'b_day']

class EmployeeSchema(ModelSchema):
    class Meta:
        model = Employee
        fields = ['id_employee', 'fio', 'rank', 'phone_number']

class OrderSchema(ModelSchema):
    class Meta:
        model = Order
        fields = "__all__"

# Для продажи часто нужно видеть не просто ID сотрудника, а его ФИО.
# Сделаем вложенную схему (это продвинутый уровень, но очень полезный)
class SaleSchema(ModelSchema):
    # Переопределяем поле, чтобы Ninja автоматически подтянул данные связанного объекта
    ip_employee: EmployeeSchema
    passport_client: ClientSchema

    class Meta:
        model = Sale
        fields = ['id_sale', 'sale_date', 'end_price', 'ip_employee', 'passport_client']

# ==========================================
# 2. ЭНДПОИНТЫ ДЛЯ АВТОМОБИЛЕЙ
# ==========================================

@api.get("/cars", response=List[CarSchema])
@paginate # Добавляет пагинацию (страницы), если машин очень много
def get_cars(request, status: Optional[str] = None):
    """
    Получить список всех авто.
    Можно фильтровать по ?status=В наличии
    """
    cars = Car.objects.all()
    if status:
        cars = cars.filter(car_status=status)
    return cars

@api.get("/cars/{vin}", response=CarSchema)
def get_car_by_vin(request, vin: str):
    """Получить информацию об одном авто по VIN"""
    return get_object_or_404(Car, vin=vin)

@api.post("/cars", response=CarSchema)
def create_car(request, data: CarSchema):
    """Добавить новый автомобиль"""
    # **data.dict() распаковывает JSON в аргументы
    car = Car.objects.create(**data.dict())
    return car

# ==========================================
# 3. ЭНДПОИНТЫ ДЛЯ КЛИЕНТОВ
# ==========================================

@api.get("/clients", response=List[ClientSchema])
@paginate
def get_clients(request, search: Optional[str] = None):
    """Поиск клиента по ФИО"""
    clients = Client.objects.all()
    if search:
        # icontains = поиск по части слова (нечувствительно к регистру)
        clients = clients.filter(fio__icontains=search)
    return clients

@api.post("/clients", response=ClientSchema)
def create_client(request, data: ClientSchema):
    client = Client.objects.create(**data.dict())
    return client

# ==========================================
# 4. ЭНДПОИНТЫ ДЛЯ ПРОДАЖ
# ==========================================

@api.get("/sales", response=List[SaleSchema])
@paginate
def get_sales(request):
    """
    Список продаж.
    Благодаря SaleSchema тут сразу будут видны ФИО сотрудников и клиентов, а не просто ID.
    select_related ускоряет запрос к БД.
    """
    return Sale.objects.select_related('ip_employee', 'passport_client').all()

# ==========================================
# 5. ЭНДПОИНТЫ ДЛЯ СОТРУДНИКОВ
# ==========================================

@api.get("/employees", response=List[EmployeeSchema])
def get_employees(request):
    return Employee.objects.all()