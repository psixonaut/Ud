from ninja import NinjaAPI, ModelSchema
from typing import List
from django.shortcuts import get_object_or_404
from .models import Car, Client, Sale, Employee

api = NinjaAPI(title="Auto Shop CRM API")


# --- Схемы данных ---

class CarSchema(ModelSchema):
    class Meta:
        model = Car
        fields = "__all__"


class ClientSchema(ModelSchema):
    class Meta:
        model = Client
        fields = "__all__"


class SaleSchema(ModelSchema):
    class Meta:
        model = Sale
        fields = ['id_sale', 'sale_date', 'end_price']


# --- Ручки (Endpoints) ---

@api.get("/cars", response=List[CarSchema])
def list_cars(request, status: str = None):
    qs = Car.objects.all()
    if status:
        qs = qs.filter(car_status=status)
    return qs


@api.get("/cars/{vin}", response=CarSchema)
def get_car(request, vin: str):
    return get_object_or_404(Car, vin=vin)


@api.post("/clients", response=ClientSchema)
def create_client(request, payload: ClientSchema):
    client = Client.objects.create(**payload.dict())
    return client


@api.get("/sales", response=List[SaleSchema])
def list_sales(request):
    return Sale.objects.all()


# Пример сложной логики в API: Тест-драйв
from datetime import datetime
from .models import Test_drive


class TestDriveCreateSchema(ModelSchema):
    class Meta:
        model = Test_drive
        fields = ['vin', 'passport_client', 'id_employee', 'datetime_reservation']


@api.post("/test-drive")
def create_test_drive(request, payload: TestDriveCreateSchema):
    # Данные валидируются через .clean() модели при сохранении,
    # но Django Ninja делает это неявно. Лучше вызвать full_clean()
    try:
        data = payload.dict()
        # Конвертируем ID в объекты, так как payload содержит int/str
        data['vin'] = get_object_or_404(Car, vin=data['vin'])
        data['passport_client'] = get_object_or_404(Client, passport_client=data['passport_client'])
        data['id_employee'] = get_object_or_404(Employee, id_employee=data['id_employee'])

        td = Test_drive(**data)
        td.full_clean()  # Здесь сработают все наши проверки (возраст, лимиты, статус авто)
        td.save()
        return {"id": td.id_test, "status": "created"}
    except Exception as e:
        return api.create_response(request, {"error": str(e)}, status=400)