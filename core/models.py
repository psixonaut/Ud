from django.db import models
from django.core.exceptions import ValidationError
from django.db.models import Q
from datetime import date
from django.utils import timezone

# ВАЖНО: Все статусы с большой буквы, как требует ваша база данных!
STATUS_CHOICES = [
    ('Заказан', 'Заказан'),
    ('На заводе', 'На заводе'),
    ('В пути', 'В пути'),
    ('Прибыл', 'Прибыл'),
    ('В продаже', 'В продаже'),
    ('Для тест-драйвов', 'Для тест-драйвов'),
    ('Продан', 'Продан'),
]

RANK_CHOICES = [
    ('Менеджер', 'Менеджер'),
    ('Продавец-консультант', 'Продавец-консультант'),
    ('Специалист по закупкам', 'Специалист по закупкам'),
    ('Сотрудник сервиса', 'Сотрудник сервиса'),
]


class Employee(models.Model):
    id_employee = models.AutoField(db_column='idСотрудника', primary_key=True)
    fio = models.CharField(db_column='ФИО', max_length=100)
    rank = models.CharField(db_column='Должность', max_length=50, choices=RANK_CHOICES)
    phone_number = models.BigIntegerField(db_column='Номер_телефона', unique=True)
    license_number = models.BigIntegerField(db_column='Номер_ву', unique=True, blank=True, null=True)
    passport_employee = models.BigIntegerField(db_column='Паспорт_сотрудник', unique=True)
    b_date = models.DateField(db_column='Дата_рождения')
    employed = models.IntegerField(db_column='Трудоустроен', default=1)

    def clean(self):
        if self.b_date:
            today = date.today()
            age = today.year - self.b_date.year - ((today.month, today.day) < (self.b_date.month, self.b_date.day))
            if age < 18:
                raise ValidationError("Сотрудник должен быть не младше 18 лет.")

    def __str__(self):
        return self.fio

    class Meta:
        managed = True
        db_table = 'Сотрудник'
        verbose_name = 'Сотрудник'
        verbose_name_plural = 'Сотрудники'


class Client(models.Model):
    passport_client = models.BigIntegerField(db_column='Паспорт_клиент', primary_key=True)
    fio = models.CharField(db_column='ФИО', max_length=100)
    license_number = models.BigIntegerField(db_column='Номер_ву', unique=True, blank=True, null=True)
    phone_number = models.CharField(db_column='Номер_телефона', max_length=50)
    b_day = models.DateField(db_column='Дата_рождения')

    def __str__(self):
        return self.fio

    class Meta:
        managed = True
        db_table = 'Клиент'
        verbose_name = 'Клиент'
        verbose_name_plural = 'Клиенты'


class Car(models.Model):
    vin = models.CharField(db_column='VIN', primary_key=True, max_length=150)
    car_status = models.CharField(db_column='Статус_автомобиля', max_length=100, choices=STATUS_CHOICES,
                                  default='Заказан')
    make = models.CharField(db_column='Марка', max_length=50)
    model = models.CharField(db_column='Модель', max_length=50)
    engine = models.CharField(db_column='Двигатель', max_length=50)
    gearbox = models.CharField(db_column='Коробка', max_length=50)
    driven_wheels = models.CharField(db_column='Привод', max_length=50)
    body = models.CharField(db_column='Кузов', max_length=50)
    make_year = models.IntegerField(db_column='Год_производства')
    trim = models.CharField(db_column='Комплектация', max_length=50)
    addons = models.CharField(db_column='Дополнительное_оборудование', max_length=200, blank=True, null=True)
    color = models.CharField(db_column='Цвет', max_length=50)
    date_of_delivery = models.DateField(db_column='Дата_поступления', blank=True, null=True)
    price = models.IntegerField(db_column='Цена')
    discount = models.IntegerField(db_column='Скидка', blank=True, null=True, default=0)

    class Meta:
        managed = True
        db_table = 'Автомобиль'
        verbose_name = 'Автомобиль'
        verbose_name_plural = 'Автомобили'
        constraints = [
            models.CheckConstraint(check=Q(price__gt=100000), name='price_gt_100k'),
            models.CheckConstraint(check=Q(discount__lte=50), name='discount_lte_50'),
        ]

    def __str__(self):
        return f"{self.make} {self.model} ({self.vin})"


class Order(models.Model):
    id_order = models.AutoField(db_column='idЗаказа', primary_key=True)
    id_employee = models.ForeignKey(Employee, models.DO_NOTHING, db_column='idСотрудника')
    date_order = models.DateField(db_column='Дата_заказа', auto_now_add=True)
    state_order = models.CharField(db_column='Статус_заказа', max_length=100, default='Заказан')
    make = models.CharField(db_column='Марка', max_length=50)
    model = models.CharField(db_column='Модель', max_length=50)
    engine = models.CharField(db_column='Двигатель', max_length=50)
    gearbox = models.CharField(db_column='Коробка', max_length=50)
    driven_wheels = models.CharField(db_column='Привод', max_length=50)
    body = models.CharField(db_column='Кузов', max_length=50)
    make_year = models.IntegerField(db_column='Год_производства')
    trim = models.CharField(db_column='Комплектация', max_length=50)
    addons = models.CharField(db_column='Дополнительное_оборудование', max_length=200)
    amount = models.IntegerField(db_column='Количество', default=1)

    expected_delivery = models.DateField(null=True, blank=True)

    def clean(self):
        if self.id_employee.rank != 'Менеджер':
            raise ValidationError("Оформлять заказы могут только сотрудники с должностью 'Менеджер'.")
        if self.expected_delivery and self.date_order and self.date_order > self.expected_delivery:
            raise ValidationError("Дата заказа должна быть меньше даты поставки.")

    class Meta:
        managed = True
        db_table = 'Заказ'
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'


class Sale(models.Model):
    id_sale = models.AutoField(db_column='idПродажи', primary_key=True)
    ip_employee = models.ForeignKey(Employee, models.DO_NOTHING, db_column='idСотрудника')
    passport_client = models.ForeignKey(Client, models.DO_NOTHING, db_column='Паспорт_клиент')
    sale_date = models.DateField(db_column='Дата_продажи', default=timezone.now)
    end_price = models.BigIntegerField(db_column='Итоговая_сумма', default=0)

    def __str__(self):
        return f"Продажа №{self.id_sale}"

    class Meta:
        managed = True
        db_table = 'Продажа'
        verbose_name = 'Продажа'
        verbose_name_plural = 'Продажи'


class Sale_list(models.Model):
    id_sale = models.OneToOneField(Sale, models.DO_NOTHING, db_column='idПродажи', primary_key=True)
    vin = models.ForeignKey(Car, models.DO_NOTHING, db_column='VIN')
    discounted_prise = models.BigIntegerField(db_column='Цена_со_скидкой')

    def clean(self):
        # Важно: тут статус тоже должен быть с Большой буквы
        if self.vin.car_status != 'В продаже':
            raise ValidationError(
                f"Автомобиль {self.vin.vin} имеет статус '{self.vin.car_status}', продажа невозможна.")

    class Meta:
        managed = True
        db_table = 'Состав_продажи'
        unique_together = (('id_sale', 'vin'),)
        verbose_name = 'Состав продажи'
        verbose_name_plural = 'Состав продаж'


class Test_drive(models.Model):
    id_test = models.AutoField(db_column='idТест_драйва', primary_key=True)
    vin = models.ForeignKey(Car, models.DO_NOTHING, db_column='VIN')
    passport_client = models.ForeignKey(Client, models.DO_NOTHING, db_column='Паспорт_клиент')
    id_employee = models.ForeignKey(Employee, models.DO_NOTHING, db_column='idСотрудника')
    datetime_reservation = models.DateTimeField(db_column='ДатаВремя_брони')
    result = models.CharField(db_column='Итог', max_length=20, blank=True, null=True)

    def clean(self):
        # Статус с большой буквы
        if self.vin.car_status != 'Для тест-драйвов':
            raise ValidationError("Этот автомобиль не предназначен для тест-драйва.")

        if self.passport_client.b_day:
            today = date.today()
            age = today.year - self.passport_client.b_day.year
            if age < 21:
                raise ValidationError("Клиент должен быть старше 21 года.")

        if self.pk:
            old_obj = Test_drive.objects.get(pk=self.pk)
            days_diff = (self.datetime_reservation.date() - date.today()).days
            if old_obj.datetime_reservation != self.datetime_reservation and days_diff < 2:
                raise ValidationError("Нельзя менять дату бронирования менее чем за 2 дня.")

        day_start = self.datetime_reservation.replace(hour=0, minute=0, second=0)
        day_end = self.datetime_reservation.replace(hour=23, minute=59, second=59)
        count = Test_drive.objects.filter(
            id_employee=self.id_employee,
            datetime_reservation__range=(day_start, day_end)
        ).exclude(pk=self.pk).count()

        if count >= 5:
            raise ValidationError("У этого сотрудника уже 5 тест-драйвов на этот день.")

    class Meta:
        managed = True
        db_table = 'Тест_драйв'
        verbose_name = 'Тест-драйв'
        verbose_name_plural = 'Тест-драйвы'