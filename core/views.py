from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.db.models import Count, Sum
from .models import *
from .forms import *


def user_login(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            fio = form.cleaned_data['fio']
            password = form.cleaned_data['password']
            try:
                # Ищем сотрудника по ФИО
                employee = Employee.objects.get(fio=fio)
                if employee.user:
                    user = authenticate(username=employee.user.username, password=password)
                    if user:
                        login(request, user)
                        return redirect('dashboard')
                messages.error(request, "Неверный пароль или пользователь не привязан")
            except Employee.DoesNotExist:
                messages.error(request, "Сотрудник с таким ФИО не найден")
    else:
        form = LoginForm()
    return render(request, 'login.html', {'form': form})


def user_logout(request):
    logout(request)
    return redirect('login')


@login_required
def dashboard(request):
    try:
        employee = request.user.employee_profile
    except:
        return render(request, 'error.html', {'message': "Ваш профиль не связан с сотрудником."})

    context = {'employee': employee}

    # Статистика для дашборда
    if employee.rank in ['Менеджер', 'Специалист по закупкам']:
        context['sales_count'] = Sale.objects.count()
        context['total_revenue'] = Sale.objects.aggregate(Sum('end_price'))['end_price__sum'] or 0
        context['cars_in_stock'] = Car.objects.filter(car_status='В продаже').count()

    return render(request, 'dashboard.html', context)


# --- АВТОМОБИЛИ ---
@login_required
def car_list(request):
    cars = Car.objects.all()
    # Фильтрация
    status = request.GET.get('status')
    if status:
        cars = cars.filter(car_status=status)
    return render(request, 'car_list.html', {'cars': cars})


# --- ЗАКАЗЫ (Только закупки) ---
@login_required
def order_list(request):
    employee = request.user.employee_profile
    if employee.rank != 'Специалист по закупкам':
        return redirect('dashboard')

    orders = Order.objects.all().order_by('-date_order')
    return render(request, 'order_list.html', {'orders': orders})


@login_required
def create_order(request):
    employee = request.user.employee_profile
    if employee.rank != 'Специалист по закупкам': return redirect('dashboard')

    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.id_employee = employee
            order.save()
            messages.success(request, "Заказ оформлен!")
            return redirect('order_list')
    else:
        form = OrderForm()
    return render(request, 'form_base.html', {'form': form, 'title': 'Новый заказ'})


@login_required
def accept_car(request, order_id):
    """Перевод из заказа в наличие"""
    order = get_object_or_404(Order, pk=order_id)
    if request.method == 'POST':
        form = CarArrivalForm(request.POST)
        if form.is_valid():
            # Создаем машину на основе заказа
            Car.objects.create(
                vin=form.cleaned_data['vin'],
                color=form.cleaned_data['color'],
                price=form.cleaned_data['price'],
                date_of_delivery=form.cleaned_data['date_of_delivery'],
                car_status='В продаже',
                make=order.make, model=order.model, engine=order.engine,
                gearbox=order.gearbox, driven_wheels=order.driven_wheels,
                body=order.body, make_year=order.make_year, trim=order.trim,
                addons=order.addons
            )
            # Меняем статус заказа
            order.state_order = 'Оформлен'
            order.save()
            messages.success(request, "Автомобиль принят на склад!")
            return redirect('order_list')
    else:
        form = CarArrivalForm()
    return render(request, 'form_base.html', {'form': form, 'title': 'Приемка автомобиля'})


# --- ПРОДАЖИ ---
@login_required
def create_sale(request):
    employee = request.user.employee_profile
    if request.method == 'POST':
        form = SaleForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # 1. Создаем продажу
                    sale = Sale.objects.create(
                        ip_employee=employee,
                        passport_client=form.cleaned_data['passport_client'],
                        end_price=0
                    )
                    # 2. Создаем состав (триггер в signals сам обновит цену)
                    car = form.cleaned_data['vin']
                    manual_price = form.cleaned_data['end_price']

                    # Если ввели цену руками, используем её
                    price = manual_price if manual_price else car.price

                    Sale_list.objects.create(id_sale=sale, vin=car, discounted_prise=price)

                    # Обновляем статус вручную (если сигнал не сработает)
                    car.car_status = 'Продан'
                    car.save()

                messages.success(request, "Продажа оформлена!")
                return redirect('dashboard')
            except Exception as e:
                messages.error(request, f"Ошибка: {e}")
    else:
        form = SaleForm()
    return render(request, 'form_base.html', {'form': form, 'title': 'Оформление продажи'})


# --- ТЕСТ-ДРАЙВЫ ---
@login_required
def test_drive_list(request):
    tds = Test_drive.objects.all().order_by('-datetime_reservation')
    return render(request, 'test_drive_list.html', {'tds': tds})


@login_required
def create_test_drive(request):
    employee = request.user.employee_profile
    if request.method == 'POST':
        form = TestDriveForm(request.POST)
        if form.is_valid():
            td = form.save(commit=False)
            td.id_employee = employee
            try:
                td.full_clean()  # Запуск валидации
                td.save()
                messages.success(request, "Запись создана")
                return redirect('test_drive_list')
            except ValidationError as e:
                form.add_error(None, e)
    else:
        form = TestDriveForm()
    return render(request, 'form_base.html', {'form': form, 'title': 'Запись на тест-драйв'})


# --- СОТРУДНИКИ И УВОЛЬНЕНИЕ ---
@login_required
def employee_list(request):
    if request.user.employee_profile.rank != 'Менеджер': return redirect('dashboard')
    employees = Employee.objects.all()
    return render(request, 'employee_list.html', {'employees': employees})


@login_required
def fire_employee(request, emp_id):
    """Мягкое удаление и переназначение дел"""
    target = get_object_or_404(Employee, pk=emp_id)

    # Ищем будущие тест-драйвы этого сотрудника
    future_tds = Test_drive.objects.filter(id_employee=target, result='Ожидается')

    if request.method == 'POST':
        form = ReassignTestDriveForm(request.POST)
        if form.is_valid():
            new_emp = form.cleaned_data['new_employee']
            # Переназначаем
            future_tds.update(id_employee=new_emp)
            # Увольняем
            target.employed = 0
            target.save()
            messages.success(request, f"Сотрудник уволен. Дела переданы {new_emp.fio}")
            return redirect('employee_list')
    else:
        form = ReassignTestDriveForm()

    return render(request, 'fire_employee.html', {'form': form, 'target': target, 'count': future_tds.count()})