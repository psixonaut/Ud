from django.db import models
from django.core.exceptions import ValidationError
from django.db.models import Q
from datetime import date
from django.utils import timezone

# --- СПРАВОЧНИКИ (Строго по Check Constraint БД) ---
STATUS_CHOICES = [
    ('В пути', 'В пути'),
    ('Прибыл', 'Прибыл'),
    ('В продаже', 'В продаже'),
    ('Для тест-драйвов', 'Для тест-драйвов'),
    ('Продан', 'Продан'),
]

# Синхронизируем статусы заказа с доступными статусами авто
ORDER_STATUS_CHOICES = [
    ('В пути', 'В пути'),
    ('Прибыл', 'Прибыл'),
    ('Продан', 'Продан'),
]

TEST_RESULT_CHOICES = [
    ('Ожидается', 'Ожидается'),
    ('Успешно', 'Успешно'),
    ('Клиент думает', 'Клиент думает'),
    ('Отказ', 'Отказ'),
    ('Купил', 'Купил'),
]

GEARBOX_CHOICES = [
    ('MT', 'Механика (MT)'),
    ('AT', 'Автомат (AT)'),
    ('CVT', 'Вариатор (CVT)'),
    ('DCT', 'Робот (DCT)')
]

DRIVE_CHOICES = [
    ('передний', 'Передний'),
    ('задний', 'Задний'),
    ('полный', 'Полный')
]

RANK_CHOICES = [
    ('Менеджер', 'Менеджер'),
    ('Продавец-консультант', 'Продавец-консультант'),
    ('Специалист по закупкам', 'Специалист по закупкам'),
    ('Сотрудник приёма и предпродажной подготовки', 'Сотрудник приёма и предпродажной подготовки')]

# --- МОДЕЛИ ---

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
            if age < 18: raise ValidationError("Сотрудник должен быть не младше 18 лет.")

    def __str__(self): return f"{self.fio} ({self.rank})"
    class Meta: managed = False; db_table = 'Сотрудник'; verbose_name = 'Сотрудник'; verbose_name_plural = 'Сотрудники'


class Client(models.Model):
    passport_client = models.BigIntegerField(db_column='Паспорт_клиент', primary_key=True)
    fio = models.CharField(db_column='ФИО', max_length=100)
    license_number = models.BigIntegerField(db_column='Номер_ву', unique=True, blank=True, null=True)
    phone_number = models.CharField(db_column='Номер_телефона', max_length=50)
    b_day = models.DateField(db_column='Дата_рождения')

    def __str__(self): return self.fio
    class Meta: managed = False; db_table = 'Клиент'; verbose_name = 'Клиент'; verbose_name_plural = 'Клиенты'


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

    def clean(self):
        current_year = date.today().year

        # 1. Проверка на будущее
        if self.make_year and self.make_year > current_year:
            raise ValidationError(
                f"Год производства ({self.make_year}) не может быть больше текущего ({current_year}).")

        # 2. НОВАЯ ПРОВЕРКА: Не меньше 1900
        if self.make_year and self.make_year < 1900:
            raise ValidationError(f"Год производства ({self.make_year}) не может быть меньше 1900 года.")

        # 3. Проверка скидки
        if self.discount and self.discount > 50:
            raise ValidationError("Скидка не может превышать 50%.")

        # 4. Проверка цены
        if self.price and self.discount is not None:
            final_price = self.price * (1 - self.discount / 100)
            if final_price < 100000:
                raise ValidationError(f"Цена со скидкой ({int(final_price)}) не может быть меньше 100,000 руб.")

        # 5. Проверка ручного статуса
        if self.pk and self.car_status == 'Продан':
            is_sold_officially = Sale_list.objects.filter(vin=self.pk).exists()
            if not is_sold_officially:
                raise ValidationError(
                    "Нельзя вручную установить статус 'Продан'. Оформите продажу через меню 'Продажи'.")

    class Meta:
        managed = False; db_table = 'Автомобиль'; verbose_name = 'Автомобиль'; verbose_name_plural = 'Автомобили'

    def __str__(self):
        return f"{self.make} {self.model} ({self.vin})"


class Order(models.Model):
    id_order = models.AutoField(db_column='idЗаказа', primary_key=True)
    id_employee = models.ForeignKey(Employee, models.DO_NOTHING, db_column='idСотрудника')
    date_order = models.DateField(db_column='Дата_заказа', auto_now_add=True)
    # ИЗМЕНЕНО: default='В пути'
    state_order = models.CharField(db_column='Статус_заказа', max_length=100, choices=ORDER_STATUS_CHOICES, default='В пути')
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

    def clean(self):
        # ИЗМЕНЕНИЕ: Проверяем на 'Специалист по закупкам' вместо 'Менеджер'
        if self.id_employee.rank != 'Специалист по закупкам':
            raise ValidationError("Оформлять заказы могут только сотрудники с должностью 'Специалист по закупкам'.")

        if self.amount < 1:
            raise ValidationError("Количество должно быть не менее 1.")

    class Meta:
        managed = False; db_table = 'Заказ'; verbose_name = 'Заказ'; verbose_name_plural = 'Заказы'


class Sale(models.Model):
    id_sale = models.AutoField(db_column='idПродажи', primary_key=True)

    # ИЗМЕНЕНИЕ: Добавлен limit_choices_to
    ip_employee = models.ForeignKey(
        Employee,
        models.DO_NOTHING,
        db_column='idСотрудника',
        limit_choices_to={'rank__in': ['Менеджер', 'Продавец-консультант']}
    )

    passport_client = models.ForeignKey(Client, models.DO_NOTHING, db_column='Паспорт_клиент')
    sale_date = models.DateField(db_column='Дата_продажи', default=timezone.now)
    end_price = models.BigIntegerField(db_column='Итоговая_сумма', default=0)

    def clean(self):
        # ИЗМЕНЕНИЕ: Проверка должности сотрудника
        allowed_ranks = ['Менеджер', 'Продавец-консультант']
        if self.ip_employee.rank not in allowed_ranks:
            raise ValidationError(
                f"Сотрудник {self.ip_employee.fio} (должность: {self.ip_employee.rank}) не имеет права оформлять продажи.")

    def __str__(self):
        return f"Продажа №{self.id_sale}"

    class Meta:
        managed = False
        db_table = 'Продажа'
        verbose_name = 'Продажа'
        verbose_name_plural = 'Продажи'


class Sale_list(models.Model):
    id_sale = models.ForeignKey(Sale, models.DO_NOTHING, db_column='idПродажи')
    vin = models.OneToOneField(Car, models.DO_NOTHING, db_column='VIN', primary_key=True, limit_choices_to={'car_status': 'В продаже'})
    discounted_prise = models.BigIntegerField(db_column='Цена_со_скидкой', blank=True, null=True)

    def clean(self):
        if hasattr(self, 'vin') and self.vin.car_status != 'В продаже':
            raise ValidationError(f"Автомобиль {self.vin.vin} имеет статус '{self.vin.car_status}', продажа невозможна.")
        if hasattr(self, 'vin'):
            if self.discounted_prise is None:
                if self.vin.discount and self.vin.discount > 0:
                    calc_price = self.vin.price * (1 - self.vin.discount / 100)
                else:
                    calc_price = self.vin.price
                self.discounted_prise = int(calc_price)
            if self.discounted_prise < 100000:
                raise ValidationError(f"Итоговая цена ({self.discounted_prise}) не может быть меньше 100 000 руб.")

    class Meta: managed = False; db_table = 'Состав_продажи'; verbose_name = 'Состав продажи'; verbose_name_plural = 'Состав продаж'


class Test_drive(models.Model):
    id_test = models.AutoField(db_column='idТест_драйва', primary_key=True)

    vin = models.ForeignKey(
        Car,
        models.DO_NOTHING,
        db_column='VIN',
        limit_choices_to={'car_status': 'Для тест-драйвов'},
        blank=False,
        null=False
    )

    passport_client = models.ForeignKey(
        Client,
        models.DO_NOTHING,
        db_column='Паспорт_клиент',
        limit_choices_to={'license_number__isnull': False},
        blank=False,
        null=False
    )

    # ИЗМЕНЕНИЕ ЗДЕСЬ: Фильтр по правам И по должности
    id_employee = models.ForeignKey(
        Employee,
        models.DO_NOTHING,
        db_column='idСотрудника',
        limit_choices_to={
            'license_number__isnull': False,
            'rank__in': ['Менеджер', 'Продавец-консультант']
        },
        blank=False,
        null=False
    )

    datetime_reservation = models.DateTimeField(db_column='ДатаВремя_брони', blank=False, null=False)
    result = models.CharField(db_column='Итог', max_length=20, choices=TEST_RESULT_CHOICES, default='Ожидается',
                              blank=False, null=False)

    def clean(self):
        # 1. Проверка прав сотрудника
        if hasattr(self, 'id_employee'):
            if not self.id_employee.license_number:
                raise ValidationError(f"Сотрудник {self.id_employee.fio} не имеет прав.")

            # 2. НОВАЯ ПРОВЕРКА: Проверка должности
            allowed_ranks = ['Менеджер', 'Продавец-консультант']
            if self.id_employee.rank not in allowed_ranks:
                raise ValidationError(
                    f"Сотрудник {self.id_employee.fio} (должность: {self.id_employee.rank}) не имеет права проводить тест-драйвы.")

        # Проверка клиента
        if hasattr(self, 'passport_client'):
            if not self.passport_client.license_number:
                raise ValidationError(f"У клиента {self.passport_client.fio} отсутствуют права.")
            if self.passport_client.b_day:
                today = date.today()
                age = today.year - self.passport_client.b_day.year - (
                            (today.month, today.day) < (self.passport_client.b_day.month,
                                                        self.passport_client.b_day.day))
                if age < 21: raise ValidationError("Клиент должен быть старше 21 года.")

        # Проверка статуса авто
        if hasattr(self, 'vin') and self.vin.car_status != 'Для тест-драйвов':
            raise ValidationError("Этот автомобиль не предназначен для тест-драйва.")

        # Проверка изменения даты
        if self.pk:
            old_obj = Test_drive.objects.get(pk=self.pk)
            days_diff = (self.datetime_reservation.date() - date.today()).days
            if old_obj.datetime_reservation != self.datetime_reservation and days_diff < 2:
                raise ValidationError("Нельзя менять дату бронирования менее чем за 2 дня.")

        # Проверка лимита (5 в день)
        if self.datetime_reservation and hasattr(self, 'id_employee'):
            day_start = self.datetime_reservation.replace(hour=0, minute=0, second=0)
            day_end = self.datetime_reservation.replace(hour=23, minute=59, second=59)
            count = Test_drive.objects.filter(id_employee=self.id_employee,
                                              datetime_reservation__range=(day_start, day_end)).exclude(
                pk=self.pk).count()
            if count >= 5: raise ValidationError("У этого сотрудника уже 5 тест-драйвов на этот день.")

    class Meta:
        managed = False; db_table = 'Тест_драйв'; verbose_name = 'Тест-драйв'; verbose_name_plural = 'Тест-драйвы'