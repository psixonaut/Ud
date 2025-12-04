from django.db import models
from django.core.exceptions import ValidationError
from django.db.models import Q
from datetime import date
from django.utils import timezone

# --- СПРАВОЧНИКИ (Для выпадающих списков) ---

# Статусы автомобиля (как в базе)
STATUS_CHOICES = [
    ('Заказан', 'Заказан'),
    ('На заводе', 'На заводе'),
    ('В пути', 'В пути'),
    ('Прибыл', 'Прибыл'),
    ('В продаже', 'В продаже'),
    ('Для тест-драйвов', 'Для тест-драйвов'),
    ('Продан', 'Продан'),
]

# Статусы заказа
ORDER_STATUS_CHOICES = [
    ('Заказан', 'Заказан'),
    ('На заводе', 'На заводе'),
    ('В пути', 'В пути'),
    ('Прибыл', 'Прибыл'),
    ('Продан', 'Продан'),  # Если заказ завершен
]

# Коробка передач (Значения из PDF/Логов)
GEARBOX_CHOICES = [
    ('MT', 'Механика (MT)'),
    ('AT', 'Автомат (AT)'),
    ('CVT', 'Вариатор (CVT)'),
    ('DCT', 'Робот (DCT)'),
]

# Привод (Значения должны быть с маленькой буквы, судя по твоим логам "полный")
DRIVE_CHOICES = [
    ('передний', 'Передний'),
    ('задний', 'Задний'),
    ('полный', 'Полный'),
]

# Должности
RANK_CHOICES = [
    ('Менеджер', 'Менеджер'),
    ('Продавец-консультант', 'Продавец-консультант'),
    ('Специалист по закупкам', 'Специалист по закупкам'),
    ('Сотрудник сервиса', 'Сотрудник сервиса'),
]

TEST_RESULT_CHOICES = [
    ('Ожидается', 'Ожидается'),
    ('Успешно', 'Успешно'),
    ('Клиент думает', 'Клиент думает'),
    ('Отказ', 'Отказ'),
    ('Купил', 'Купил'),
]


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
            if age < 18:
                raise ValidationError("Сотрудник должен быть не младше 18 лет.")

    def __str__(self):
        return f"{self.fio} ({self.rank})"

    class Meta:
        managed = False
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
        managed = False
        db_table = 'Клиент'
        verbose_name = 'Клиент'
        verbose_name_plural = 'Клиенты'


class Car(models.Model):
    vin = models.CharField(db_column='VIN', primary_key=True, max_length=150)

    # 1. Выпадающий список Статусов
    car_status = models.CharField(db_column='Статус_автомобиля', max_length=100, choices=STATUS_CHOICES,
                                  default='Заказан')

    make = models.CharField(db_column='Марка', max_length=50)
    model = models.CharField(db_column='Модель', max_length=50)
    engine = models.CharField(db_column='Двигатель', max_length=50)

    # 2. Выпадающий список Коробки
    gearbox = models.CharField(db_column='Коробка', max_length=50, choices=GEARBOX_CHOICES)

    # 3. Выпадающий список Привода
    driven_wheels = models.CharField(db_column='Привод', max_length=50, choices=DRIVE_CHOICES)

    body = models.CharField(db_column='Кузов', max_length=50)
    make_year = models.IntegerField(db_column='Год_производства')
    trim = models.CharField(db_column='Комплектация', max_length=50)

    # 4. Дефолтное значение "Нет"
    addons = models.CharField(db_column='Дополнительное_оборудование', max_length=200, blank=True, default='Нет')

    color = models.CharField(db_column='Цвет', max_length=50)
    date_of_delivery = models.DateField(db_column='Дата_поступления', blank=True, null=True)
    price = models.IntegerField(db_column='Цена')
    discount = models.IntegerField(db_column='Скидка', blank=True, null=True, default=0)

    def clean(self):
        current_year = date.today().year
        if self.make_year and self.make_year > current_year:
            raise ValidationError(
                f"Год производства ({self.make_year}) не может быть больше текущего ({current_year}).")

    class Meta:
        managed = False
        db_table = 'Автомобиль'
        verbose_name = 'Автомобиль'
        verbose_name_plural = 'Автомобили'

    def __str__(self):
        return f"{self.make} {self.model} ({self.vin})"


class Order(models.Model):
    id_order = models.AutoField(db_column='idЗаказа', primary_key=True)
    id_employee = models.ForeignKey(Employee, models.DO_NOTHING, db_column='idСотрудника')
    date_order = models.DateField(db_column='Дата_заказа', auto_now_add=True)

    # 5. Выпадающий список для Заказа
    state_order = models.CharField(db_column='Статус_заказа', max_length=100, choices=ORDER_STATUS_CHOICES,
                                   default='Заказан')

    make = models.CharField(db_column='Марка', max_length=50)
    model = models.CharField(db_column='Модель', max_length=50)
    engine = models.CharField(db_column='Двигатель', max_length=50)

    # Здесь тоже можно добавить списки, если нужно, но в требованиях было про Автомобиль
    gearbox = models.CharField(db_column='Коробка', max_length=50, choices=GEARBOX_CHOICES)
    driven_wheels = models.CharField(db_column='Привод', max_length=50, choices=DRIVE_CHOICES)

    body = models.CharField(db_column='Кузов', max_length=50)
    make_year = models.IntegerField(db_column='Год_производства')
    trim = models.CharField(db_column='Комплектация', max_length=50)
    addons = models.CharField(db_column='Дополнительное_оборудование', max_length=200, default='Нет', blank=True)
    amount = models.IntegerField(db_column='Количество', default=1)

    def clean(self):
        if self.id_employee.rank != 'Менеджер':
            raise ValidationError("Оформлять заказы могут только сотрудники с должностью 'Менеджер'.")
        if self.amount < 1:
            raise ValidationError("Количество должно быть не менее 1.")

    class Meta:
        managed = False
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
        managed = False
        db_table = 'Продажа'
        verbose_name = 'Продажа'
        verbose_name_plural = 'Продажи'


# ... (код выше без изменений)

class Sale_list(models.Model):
    id_sale = models.OneToOneField(Sale, models.DO_NOTHING, db_column='idПродажи', primary_key=True)

    # ИЗМЕНЕНИЕ ЗДЕСЬ: Добавили limit_choices_to
    vin = models.ForeignKey(
        Car,
        models.DO_NOTHING,
        db_column='VIN',
        # В списке продажи будут только машины со статусом "В продаже"
        limit_choices_to={'car_status': 'В продаже'}
    )

    discounted_prise = models.BigIntegerField(db_column='Цена_со_скидкой')

    def clean(self):
        # Валидация на уровне кода (для безопасности)
        if self.vin.car_status != 'В продаже':
            raise ValidationError(
                f"Автомобиль {self.vin.vin} имеет статус '{self.vin.car_status}', продажа невозможна.")

    class Meta:
        managed = False
        db_table = 'Состав_продажи'
        verbose_name = 'Состав продажи'
        verbose_name_plural = 'Состав продаж'


class Test_drive(models.Model):
    id_test = models.AutoField(db_column='idТест_драйва', primary_key=True)

    # blank=False заставит Django подсвечивать поле красным, если оно пустое
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

    id_employee = models.ForeignKey(
        Employee,
        models.DO_NOTHING,
        db_column='idСотрудника',
        limit_choices_to={'license_number__isnull': False},
        blank=False,
        null=False
    )

    datetime_reservation = models.DateTimeField(
        db_column='ДатаВремя_брони',
        blank=False,
        null=False
    )

    # 2. Делаем выпадающий список и значение по умолчанию
    result = models.CharField(
        db_column='Итог',
        max_length=20,
        choices=TEST_RESULT_CHOICES,  # Подключаем список
        default='Ожидается',  # Значение при создании
        blank=False,  # Нельзя оставить пустым
        null=False
    )

    def clean(self):
        # Проверка прав у Клиента (если фильтр обошли)
        if hasattr(self, 'passport_client') and not self.passport_client.license_number:
            raise ValidationError(f"У клиента {self.passport_client.fio} отсутствуют права.")

        # Проверка прав у Сотрудника
        if hasattr(self, 'id_employee') and not self.id_employee.license_number:
            raise ValidationError(f"Сотрудник {self.id_employee.fio} не имеет прав.")

        # Проверка статуса машины
        if hasattr(self, 'vin') and self.vin.car_status != 'Для тест-драйвов':
            raise ValidationError("Этот автомобиль не предназначен для тест-драйва.")

        # Проверка возраста
        if hasattr(self, 'passport_client') and self.passport_client.b_day:
            today = date.today()
            age = today.year - self.passport_client.b_day.year - (
                        (today.month, today.day) < (self.passport_client.b_day.month, self.passport_client.b_day.day))
            if age < 21:
                raise ValidationError("Клиент должен быть старше 21 года.")

        # Проверка изменения даты (только при редактировании старой записи)
        if self.pk:
            old_obj = Test_drive.objects.get(pk=self.pk)
            days_diff = (self.datetime_reservation.date() - date.today()).days
            # Если дата изменилась И до теста осталось мало времени
            if old_obj.datetime_reservation != self.datetime_reservation and days_diff < 2:
                raise ValidationError("Нельзя менять дату бронирования менее чем за 2 дня.")

        # Проверка лимита сотрудника
        if self.datetime_reservation and hasattr(self, 'id_employee'):
            day_start = self.datetime_reservation.replace(hour=0, minute=0, second=0)
            day_end = self.datetime_reservation.replace(hour=23, minute=59, second=59)
            count = Test_drive.objects.filter(
                id_employee=self.id_employee,
                datetime_reservation__range=(day_start, day_end)
            ).exclude(pk=self.pk).count()
            if count >= 5:
                raise ValidationError("У этого сотрудника уже 5 тест-драйвов на этот день.")

    class Meta:
        managed = False
        db_table = 'Тест_драйв'
        verbose_name = 'Тест-драйв'
        verbose_name_plural = 'Тест-драйвы'