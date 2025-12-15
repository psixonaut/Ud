from django import forms
from .models import *


class LoginForm(forms.Form):
    fio = forms.CharField(label="ФИО Сотрудника", widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(label="Пароль", widget=forms.PasswordInput(attrs={'class': 'form-control'}))


class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        exclude = ['id_employee', 'date_order', 'state_order', 'amount']
        widgets = {
            'make': forms.TextInput(attrs={'class': 'form-control'}),
            'model': forms.TextInput(attrs={'class': 'form-control'}),
            'engine': forms.TextInput(attrs={'class': 'form-control'}),
            'gearbox': forms.Select(attrs={'class': 'form-select'}),
            'driven_wheels': forms.Select(attrs={'class': 'form-select'}),
            'body': forms.TextInput(attrs={'class': 'form-control'}),
            'make_year': forms.NumberInput(attrs={'class': 'form-control'}),
            'trim': forms.TextInput(attrs={'class': 'form-control'}),
            'addons': forms.TextInput(attrs={'class': 'form-control'}),
        }


class CarArrivalForm(forms.Form):
    """Форма для приемки машины из заказа"""
    vin = forms.CharField(label="VIN", max_length=150, widget=forms.TextInput(attrs={'class': 'form-control'}))
    color = forms.CharField(label="Цвет", max_length=50, widget=forms.TextInput(attrs={'class': 'form-control'}))
    price = forms.IntegerField(label="Цена продажи", widget=forms.NumberInput(attrs={'class': 'form-control'}))
    date_of_delivery = forms.DateField(label="Дата поступления",
                                       widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}))


class TestDriveForm(forms.ModelForm):
    class Meta:
        model = Test_drive
        fields = ['vin', 'passport_client', 'datetime_reservation']
        widgets = {
            'vin': forms.Select(attrs={'class': 'form-select'}),
            'passport_client': forms.Select(attrs={'class': 'form-select'}),
            'datetime_reservation': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['vin'].queryset = Car.objects.filter(car_status='Для тест-драйвов')
        self.fields['passport_client'].queryset = Client.objects.filter(license_number__isnull=False)


class SaleForm(forms.Form):
    passport_client = forms.ModelChoiceField(queryset=Client.objects.all(), label="Клиент",
                                             widget=forms.Select(attrs={'class': 'form-select'}))
    vin = forms.ModelChoiceField(queryset=Car.objects.filter(car_status='В продаже'), label="Автомобиль",
                                 widget=forms.Select(attrs={'class': 'form-select'}))
    end_price = forms.IntegerField(label="Итоговая цена (если отличается)", required=False,
                                   widget=forms.NumberInput(attrs={'class': 'form-control'}))


class EmployeeFireForm(forms.Form):
    """Форма увольнения с передачей дел"""
    new_employee = forms.ModelChoiceField(
        queryset=Employee.objects.filter(employed=1, rank__in=['Менеджер', 'Продавец-консультант']),
        label="На кого перевести будущие тест-драйвы?",
        widget=forms.Select(attrs={'class': 'form-select'})
    )