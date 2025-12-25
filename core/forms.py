from django import forms
from django.core.exceptions import ValidationError
from django.forms import formset_factory
from .models import *

ALLOWED_STATUSES = ['В продаже', 'Для тест-драйвов']

# --- 1. АВТОРИЗАЦИЯ ---
class LoginForm(forms.Form):
    fio = forms.CharField(label="ФИО Сотрудника", widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(label="Пароль", widget=forms.PasswordInput(attrs={'class': 'form-control'}))


# --- 2. ФИЛЬТР АВТОМОБИЛЕЙ ---
class CarFilterForm(forms.Form):
    search = forms.CharField(required=False, label="Поиск", widget=forms.TextInput(
        attrs={'class': 'form-control', 'placeholder': 'VIN, Марка или Модель'}))

    price_min = forms.IntegerField(required=False, label="Цена от",
                                   widget=forms.NumberInput(attrs={'class': 'form-control'}))
    price_max = forms.IntegerField(required=False, label="Цена до",
                                   widget=forms.NumberInput(attrs={'class': 'form-control'}))
    year_min = forms.IntegerField(required=False, label="Год от",
                                  widget=forms.NumberInput(attrs={'class': 'form-control'}))


    status = forms.ChoiceField(
        choices=[('', 'Все статусы')] + [s for s in STATUS_CHOICES if s[0] in ALLOWED_STATUSES],
        required=False,
        label="Статус",
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    BODY_CHOICES = [
        ('Седан', 'Седан'), ('Кроссовер', 'Кроссовер'), ('Внедорожник', 'Внедорожник'),
        ('Универсал', 'Универсал'), ('Лифтбек', 'Лифтбек'),
        ('Купе-кроссовер', 'Купе-кроссовер'), ('Фастбек', 'Фастбек'),
    ]

    gearbox = forms.MultipleChoiceField(choices=GEARBOX_CHOICES, required=False, label="Коробка",
                                        widget=forms.CheckboxSelectMultiple)
    driven_wheels = forms.MultipleChoiceField(choices=DRIVE_CHOICES, required=False, label="Привод",
                                              widget=forms.CheckboxSelectMultiple)
    body = forms.MultipleChoiceField(choices=BODY_CHOICES, required=False, label="Кузов",
                                     widget=forms.CheckboxSelectMultiple)

    SORT_CHOICES = [
        ('', 'По умолчанию'),
        ('price_asc', 'Цена (↑)'),
        ('price_desc', 'Цена (↓)'),
        ('year_desc', 'Год (новые)'),
    ]
    ordering = forms.ChoiceField(choices=SORT_CHOICES, required=False, label="Сортировка",
                                 widget=forms.Select(attrs={'class': 'form-select'}))


# --- 3. ЗАКАЗЫ И ПРИЕМКА ---
class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        exclude = ['id_employee', 'date_order', 'state_order']
        widgets = {
            'make': forms.TextInput(attrs={'class': 'form-control'}),
            'model': forms.TextInput(attrs={'class': 'form-control'}),
            'engine': forms.TextInput(attrs={'class': 'form-control'}),
            'body': forms.TextInput(attrs={'class': 'form-control'}),
            'trim': forms.TextInput(attrs={'class': 'form-control'}),
            'addons': forms.TextInput(attrs={'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),  # Виджет для количества
            'gearbox': forms.Select(attrs={'class': 'form-select'}),
            'driven_wheels': forms.Select(attrs={'class': 'form-select'}),
            'make_year': forms.NumberInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'amount': 'Количество автомобилей',
            'make': 'Марка', 'model': 'Модель', 'engine': 'Двигатель',
            'gearbox': 'Коробка', 'driven_wheels': 'Привод', 'body': 'Кузов',
            'make_year': 'Год выпуска', 'trim': 'Комплектация', 'addons': 'Доп. оборудование'
        }


class CarArrivalForm(forms.Form):
    vin = forms.CharField(label="VIN номер", widget=forms.TextInput(attrs={'class': 'form-control'}))
    color = forms.CharField(label="Цвет", widget=forms.TextInput(attrs={'class': 'form-control'}))
    price = forms.IntegerField(label="Цена продажи (₽)", widget=forms.NumberInput(attrs={'class': 'form-control'}))

CarArrivalFormSet = formset_factory(CarArrivalForm, extra=0)


# --- 4. ПРОДАЖА ---
class SaleForm(forms.Form):
    passport_client = forms.ModelChoiceField(queryset=Client.objects.all(),
                                             widget=forms.Select(attrs={'class': 'form-select'}), label="Клиент")
    vin = forms.ModelChoiceField(queryset=Car.objects.filter(car_status='В продаже'),
                                 widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_vin'}),
                                 label="Автомобиль")
    end_price = forms.IntegerField(label="Итоговая цена (0 = рассчитать автоматически)", required=False,
                                   widget=forms.NumberInput(attrs={'class': 'form-control', 'id': 'id_end_price'}))


class SaleFilterForm(forms.Form):
    search = forms.CharField(
        required=False,
        label="Поиск",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'VIN, Авто, Клиент...'})
    )

    date_from = forms.DateField(
        required=False,
        label="С даты",
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )

    date_to = forms.DateField(
        required=False,
        label="По дату",
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )

    price_min = forms.IntegerField(
        required=False,
        label="Цена от",
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )

    price_max = forms.IntegerField(
        required=False,
        label="Цена до",
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )

# --- 5. ТЕСТ-ДРАЙВЫ ---
class TestDriveForm(forms.ModelForm):
    class Meta:
        model = Test_drive
        fields = ['vin', 'passport_client', 'datetime_reservation']
        labels = {'vin': 'Автомобиль', 'passport_client': 'Клиент', 'datetime_reservation': 'Дата и время'}
        widgets = {
            'vin': forms.Select(attrs={'class': 'form-select'}),
            'passport_client': forms.Select(attrs={'class': 'form-select'}),
            'datetime_reservation': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['vin'].queryset = Car.objects.filter(car_status='Для тест-драйвов')
        self.fields['passport_client'].queryset = Client.objects.filter(license_number__isnull=False)


class TestDriveEditForm(forms.ModelForm):
    class Meta:
        model = Test_drive
        fields = ['datetime_reservation', 'result']
        labels = {
            'datetime_reservation': 'Дата и время (Оставьте пустым, чтобы не менять)',
            'result': 'Результат (Оставьте пустым, чтобы не менять)'
        }
        widgets = {
            'datetime_reservation': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'result': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Делаем поля необязательными в HTML
        self.fields['datetime_reservation'].required = False
        self.fields['result'].required = False

    def clean(self):
        cleaned_data = super().clean()

        if not cleaned_data.get('datetime_reservation'):
            cleaned_data['datetime_reservation'] = self.instance.datetime_reservation
            self.cleaned_data['datetime_reservation'] = self.instance.datetime_reservation
        if not cleaned_data.get('result'):
            cleaned_data['result'] = self.instance.result
            self.cleaned_data['result'] = self.instance.result

        return cleaned_data

class TestDriveResultOnlyForm(forms.ModelForm):
    class Meta:
        model = Test_drive
        fields = ['result']
        labels = {
            'result': 'Изменить результат'
        }
        widgets = {
            'result': forms.Select(attrs={'class': 'form-select'}),
        }

class CarReassignForm(forms.Form):
    new_car = forms.ModelChoiceField(
        queryset=Car.objects.filter(car_status='Для тест-драйвов'),
        label="Выберите другой автомобиль для переноса записей",
        widget=forms.Select(attrs={'class': 'form-select'})
    )

# --- 6. ПЕРСОНАЛ ---
class EmployeeForm(forms.ModelForm):
    password = forms.CharField(
        label="Пароль для входа",
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        help_text="Придумайте пароль"
    )

    class Meta:
        model = Employee
        fields = ['fio', 'rank', 'phone_number', 'license_number', 'passport_employee', 'b_date']
        labels = {
            'fio': 'ФИО', 'rank': 'Должность', 'phone_number': 'Телефон',
            'license_number': 'Номер ВУ', 'passport_employee': 'Паспорт', 'b_date': 'Дата рождения'
        }
        widgets = {
            'fio': forms.TextInput(attrs={'class': 'form-control'}),
            'rank': forms.Select(attrs={'class': 'form-select'}),
            'phone_number': forms.NumberInput(attrs={'class': 'form-control'}),
            'license_number': forms.NumberInput(attrs={'class': 'form-control'}),
            'passport_employee': forms.NumberInput(attrs={'class': 'form-control'}),
            'b_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

class EmployeeEditForm(forms.ModelForm):
    new_password = forms.CharField(
        label="Установить новый пароль",
        required=True,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Введите новый пароль'}),
    )

    class Meta:
        model = Employee
        fields = []

class ReassignTestDriveForm(forms.Form):
    new_employee = forms.ModelChoiceField(
        queryset=Employee.objects.filter(employed=1, rank__in=['Менеджер', 'Продавец-консультант']),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="На кого перевести дела?"
    )


# --- 7. КЛИЕНТЫ ---
class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = '__all__'
        labels = {
            'passport_client': 'Паспорт', 'fio': 'ФИО',
            'license_number': 'Номер ВУ', 'phone_number': 'Телефон', 'b_day': 'Дата рождения'
        }
        widgets = {
            'passport_client': forms.NumberInput(attrs={'class': 'form-control'}),
            'fio': forms.TextInput(attrs={'class': 'form-control'}),
            'license_number': forms.NumberInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'b_day': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

class CarEditForm(forms.ModelForm):
    class Meta:
        model = Car
        fields = ['price', 'discount', 'car_status']
        labels = {
            'price': 'Базовая цена',
            'discount': 'Скидка (%)',
            'car_status': 'Текущий статус'
        }
        widgets = {
            'price': forms.NumberInput(attrs={'class': 'form-control'}),
            'discount': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 50}),
            'car_status': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['car_status'].choices = [
            ('В продаже', 'В продаже'),
            ('Для тест-драйвов', 'Для тест-драйвов'),
        ]