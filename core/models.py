from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from datetime import date
from django.utils import timezone

# --- СПРАВОЧНИКИ ---
STATUS_CHOICES = [
    ('В пути', 'В пути'),
    ('В продаже', 'В продаже'),
    ('Для тест-драйвов', 'Для тест-драйвов'),
    ('Продан', 'Продан'),
]

ORDER_STATUS_CHOICES = [
    ('В пути', 'В пути'),
    ('Прибыл', 'Прибыл'),
    ('Оформлен', 'Оформлен'),
]

TEST_RESULT_CHOICES = [('Ожидается', 'Ожидается'), ('Успешно', 'Успешно'), ('Клиент думает', 'Клиент думает'),
                       ('Отказ', 'Отказ'), ('Купил', 'Купил')]
GEARBOX_CHOICES = [('MT', 'Механика (MT)'), ('AT', 'Автомат (AT)'), ('CVT', 'Вариатор (CVT)'), ('DCT', 'Робот (DCT)')]
DRIVE_CHOICES = [('передний', 'Передний'), ('задний', 'Задний'), ('полный', 'Полный')]
RANK_CHOICES = [('Менеджер', 'Менеджер'), ('Продавец-консультант', 'Продавец-консультант'),
                ('Специалист по закупкам', 'Специалист по закупкам'), ('Сотрудник сервиса', 'Сотрудник сервиса')]


# --- МОДЕЛИ ---

class Employee(models.Model):
    id_employee = models.AutoField(db_column='idСотрудника', primary_key=True)
    # Связь с Django User для входа в систему
    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True, db_column='user_id',
                                related_name='employee_profile')

    fio = models.CharField(db_column='ФИО', max_length=100)
    rank = models.CharField(db_column='Должность', max_length=50, choices=RANK_CHOICES)
    phone_number = models.BigIntegerField(db_column='Номер_телефона', unique=True)
    license_number = models.BigIntegerField(db_column='Номер_ву', unique=True, blank=True, null=True)
    passport_employee = models.BigIntegerField(db_column='Паспорт_сотрудник', unique=True)
    b_date = models.DateField(db_column='Дата_рождения')
    employed = models.IntegerField(db_column='Трудоустроен', default=1)

    def __str__(self):
        # Сортировка по алфавиту будет работать, поиск по ID тоже (если ввести цифру)
        return f"{self.fio} (ID: {self.pk})"

    class Meta: managed = False; db_table = 'Сотрудник'


class Client(models.Model):
    passport_client = models.BigIntegerField(db_column='Паспорт_клиент', primary_key=True)
    fio = models.CharField(db_column='ФИО', max_length=100)
    license_number = models.BigIntegerField(db_column='Номер_ву', unique=True, blank=True, null=True)
    phone_number = models.CharField(db_column='Номер_телефона', max_length=50)
    b_day = models.DateField(db_column='Дата_рождения')

    def __str__(self):
        return f"{self.fio} (Паспорт: {self.passport_client})"
    class Meta:
        managed = False
        db_table = 'Клиент'
        ordering = ['fio'] # Сортировка по алфавиту в выпадающих списках


class Car(models.Model):
    vin = models.CharField(db_column='VIN', primary_key=True, max_length=150)
    car_status = models.CharField(db_column='Статус_автомобиля', max_length=100, choices=STATUS_CHOICES,
                                  default='В пути')
    make = models.CharField(db_column='Марка', max_length=50)
    model = models.CharField(db_column='Модель', max_length=50)
    engine = models.CharField(db_column='Двигатель', max_length=50)
    gearbox = models.CharField(db_column='Коробка', max_length=50, choices=GEARBOX_CHOICES)
    driven_wheels = models.CharField(db_column='Привод', max_length=50, choices=DRIVE_CHOICES)
    body = models.CharField(db_column='Кузов', max_length=50)
    make_year = models.IntegerField(db_column='Год_производства')
    trim = models.CharField(db_column='Комплектация', max_length=50)
    addons = models.CharField(db_column='Дополнительное_оборудование', max_length=200, blank=True, default='Нет')
    color = models.CharField(db_column='Цвет', max_length=50)
    date_of_delivery = models.DateField(db_column='Дата_поступления', blank=True, null=True)
    price = models.IntegerField(db_column='Цена')
    discount = models.IntegerField(db_column='Скидка', blank=True, null=True, default=0)

    # (Ваш метод clean сохраняется здесь, сократил для места)

    def __str__(self):
        # В списке будет: "BMW X5 (VIN: WBA...)" - поиск сработает и по марке, и по VIN
        return f"{self.make} {self.model} (VIN: {self.vin})"
    class Meta:
        managed = False
        db_table = 'Автомобиль'
        ordering = ['make', 'model'] # Сортировка по алфавиту


class Order(models.Model):
    id_order = models.AutoField(db_column='idЗаказа', primary_key=True)
    id_employee = models.ForeignKey(Employee, models.DO_NOTHING, db_column='idСотрудника')
    date_order = models.DateField(db_column='Дата_заказа', auto_now_add=True)
    state_order = models.CharField(db_column='Статус_заказа', max_length=100, choices=ORDER_STATUS_CHOICES,
                                   default='В пути')
    make = models.CharField(db_column='Марка', max_length=50)
    model = models.CharField(db_column='Модель', max_length=50)
    engine = models.CharField(db_column='Двигатель', max_length=50)
    gearbox = models.CharField(db_column='Коробка', max_length=50, choices=GEARBOX_CHOICES)
    driven_wheels = models.CharField(db_column='Привод', max_length=50, choices=DRIVE_CHOICES)
    body = models.CharField(db_column='Кузов', max_length=50)
    make_year = models.IntegerField(db_column='Год_производства')
    trim = models.CharField(db_column='Комплектация', max_length=50)
    addons = models.CharField(db_column='Дополнительное_оборудование', max_length=200, default='Нет', blank=True)
    amount = models.IntegerField(db_column='Количество', default=1)

    class Meta: managed = False; db_table = 'Заказ'


class Sale(models.Model):
    id_sale = models.AutoField(db_column='idПродажи', primary_key=True)
    ip_employee = models.ForeignKey(Employee, models.DO_NOTHING, db_column='idСотрудника')
    passport_client = models.ForeignKey(Client, models.DO_NOTHING, db_column='Паспорт_клиент')
    sale_date = models.DateField(db_column='Дата_продажи', default=timezone.now)
    end_price = models.BigIntegerField(db_column='Итоговая_сумма', default=0)

    class Meta: managed = False; db_table = 'Продажа'


class Sale_list(models.Model):
    id_sale = models.ForeignKey(Sale, models.DO_NOTHING, db_column='idПродажи')
    vin = models.OneToOneField(Car, models.DO_NOTHING, db_column='VIN', primary_key=True)
    discounted_prise = models.BigIntegerField(db_column='Цена_со_скидкой')

    class Meta: managed = False; db_table = 'Состав_продажи'


class Test_drive(models.Model):
    id_test = models.AutoField(db_column='idТест_драйва', primary_key=True)
    vin = models.ForeignKey(Car, models.DO_NOTHING, db_column='VIN')
    passport_client = models.ForeignKey(Client, models.DO_NOTHING, db_column='Паспорт_клиент')
    id_employee = models.ForeignKey(Employee, models.DO_NOTHING, db_column='idСотрудника')
    datetime_reservation = models.DateTimeField(db_column='ДатаВремя_брони')
    result = models.CharField(db_column='Итог', max_length=20, choices=TEST_RESULT_CHOICES, default='Ожидается')

    class Meta: managed = False; db_table = 'Тест_драйв'