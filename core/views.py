from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.db.models import Sum, Count, Case, When, Value, IntegerField, Q
from django.core.exceptions import ValidationError
from .models import *
from .forms import *


# ==========================================
# 1. АВТОРИЗАЦИЯ И ГЛАВНАЯ
# ==========================================

def custom_login(request):
    """
    Вход в систему по ФИО сотрудника и паролю.
    """
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            fio = form.cleaned_data['fio'].strip()
            password = form.cleaned_data['password']
            try:
                # 1. Ищем сотрудника
                employee = Employee.objects.get(fio__iexact=fio)

                # 2. ПРОВЕРКА: Не уволен ли он?
                if employee.employed == 0:
                    messages.error(request, "⛔ Доступ запрещен: Сотрудник уволен.")
                    return render(request, 'login.html', {'form': form})

                # 3. Проверяем привязку
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
    """Главная панель со статистикой"""
    try:
        employee = request.user.employee_profile
    except:
        messages.error(request, "Профиль не связан с сотрудником.")
        return redirect('logout')

    context = {'employee': employee}

    # Статистика только для руководства и закупок
    if employee.rank in ['Менеджер', 'Специалист по закупкам']:
        context['sales_count'] = Sale.objects.count()
        context['total_revenue'] = Sale.objects.aggregate(Sum('end_price'))['end_price__sum'] or 0
        context['cars_in_stock'] = Car.objects.filter(car_status='В продаже').count()

    return render(request, 'dashboard.html', context)


# ==========================================
# 2. АВТОМОБИЛИ
# ==========================================

@login_required
def car_list(request):
    cars = Car.objects.all()
    form = CarFilterForm(request.GET)

    if form.is_valid():
        # Поиск
        if form.cleaned_data['search']:
            search = form.cleaned_data['search']
            cars = cars.filter(Q(vin__icontains=search) | Q(make__icontains=search) | Q(model__icontains=search))

        # Простые фильтры
        if form.cleaned_data['status']: cars = cars.filter(car_status=form.cleaned_data['status'])
        if form.cleaned_data['price_min']: cars = cars.filter(price__gte=form.cleaned_data['price_min'])
        if form.cleaned_data['price_max']: cars = cars.filter(price__lte=form.cleaned_data['price_max'])
        if form.cleaned_data['year_min']: cars = cars.filter(make_year__gte=form.cleaned_data['year_min'])

        # ЧЕКБОКСЫ (Множественный выбор)
        # Если выбрано хоть что-то, фильтруем по вхождению в список (IN)
        if form.cleaned_data['gearbox']:
            cars = cars.filter(gearbox__in=form.cleaned_data['gearbox'])

        if form.cleaned_data['driven_wheels']:
            cars = cars.filter(driven_wheels__in=form.cleaned_data['driven_wheels'])

        if form.cleaned_data['body']:
            cars = cars.filter(body__in=form.cleaned_data['body'])

        # Сортировка
        ordering = form.cleaned_data.get('ordering')
        if ordering == 'price_asc':
            cars = cars.order_by('price')
        elif ordering == 'price_desc':
            cars = cars.order_by('-price')
        elif ordering == 'year_desc':
            cars = cars.order_by('-make_year')
        else:
            # Дефолтная умная сортировка
            cars = cars.annotate(
                status_order=Case(
                    When(car_status='В продаже', then=Value(1)),
                    When(car_status='Для тест-драйвов', then=Value(2)),
                    When(car_status='Прибыл', then=Value(3)),
                    When(car_status='В пути', then=Value(4)),
                    When(car_status='Продан', then=Value(5)),
                    default=Value(6),
                    output_field=IntegerField(),
                )
            ).order_by('status_order', 'make', 'model')
    else:
        # Дефолтная сортировка при пустой форме
        cars = cars.annotate(
            status_order=Case(
                When(car_status='В продаже', then=Value(1)),
                When(car_status='Для тест-драйвов', then=Value(2)),
                When(car_status='Прибыл', then=Value(3)),
                When(car_status='В пути', then=Value(4)),
                When(car_status='Продан', then=Value(5)),
                default=Value(6),
                output_field=IntegerField(),
            )
        ).order_by('status_order', 'make', 'model')

    return render(request, 'car_list.html', {'cars': cars, 'form': form})


@login_required
def car_detail(request, vin):
    """Карточка автомобиля с историей"""
    car = get_object_or_404(Car, pk=vin)
    history = Test_drive.objects.filter(vin=car).order_by('-datetime_reservation')
    return render(request, 'detail_car.html', {'car': car, 'history': history})


# ==========================================
# 3. ЗАКУПКИ
# ==========================================

@login_required
def order_list(request):
    employee = request.user.employee_profile
    if employee.rank != 'Специалист по закупкам':
        return redirect('dashboard')

    orders = Order.objects.all().order_by('-date_order')
    return render(request, 'order_list.html', {'orders': orders})


@login_required
def order_detail(request, order_id):
    """Карточка заказа"""
    order = get_object_or_404(Order, pk=order_id)
    return render(request, 'detail_order.html', {'order': order})


@login_required
def create_order(request):
    employee = request.user.employee_profile
    if employee.rank != 'Специалист по закупкам':
        return redirect('dashboard')

    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.id_employee = employee
            order.save()
            messages.success(request, f"✅ Заказ на {order.amount} шт. успешно оформлен!")
            return redirect('order_list')
    else:
        form = OrderForm()
    return render(request, 'form_base.html', {'form': form, 'title': 'Создание заказа на поставку'})


@login_required
def accept_car(request, order_id):
    """
    Массовая приемка автомобилей.
    Генерирует столько форм, сколько машин указано в заказе.
    """
    order = get_object_or_404(Order, pk=order_id)

    if order.state_order == 'Оформлен':
        messages.warning(request, "Этот заказ уже принят на склад.")
        return redirect('order_list')

    # Создаем класс набора форм (FormSet)
    # extra=order.amount означает, что будет ровно столько форм, сколько машин
    CarFormSet = formset_factory(CarArrivalForm, extra=order.amount)

    if request.method == 'POST':
        formset = CarFormSet(request.POST)
        if formset.is_valid():
            try:
                with transaction.atomic():
                    # Проходим по каждой заполненной форме
                    for form in formset:
                        Car.objects.create(
                            vin=form.cleaned_data['vin'],
                            color=form.cleaned_data['color'],
                            price=form.cleaned_data['price'],
                            date_of_delivery=form.cleaned_data['date_of_delivery'],
                            car_status='В продаже',
                            # Общие данные из заказа
                            make=order.make, model=order.model, engine=order.engine,
                            gearbox=order.gearbox, driven_wheels=order.driven_wheels,
                            body=order.body, make_year=order.make_year, trim=order.trim,
                            addons=order.addons
                        )

                    # Закрываем заказ
                    order.state_order = 'Оформлен'
                    order.save()

                messages.success(request, f"✅ Успешно принято {order.amount} автомобилей на склад!")
                return redirect('order_list')
            except Exception as e:
                messages.error(request, f"Ошибка при сохранении: {e}")
                # Если ошибка, нужно вернуть форму с введенными данными
    else:
        formset = CarFormSet()

    return render(request, 'form_accept_mass.html', {
        'formset': formset,
        'order': order,
        'title': f'Приемка партии: {order.make} {order.model} ({order.amount} шт.)'
    })


@login_required
def edit_car(request, vin):
    """Редактирование цены, скидки и статуса авто"""
    # Доступ только для Менеджеров и Продавцов
    if request.user.employee_profile.rank not in ['Менеджер', 'Продавец-консультант']:
        messages.error(request, "У вас нет прав на редактирование автомобилей.")
        return redirect('car_detail', vin=vin)

    car = get_object_or_404(Car, pk=vin)

    # Нельзя редактировать проданные машины
    if car.car_status == 'Продан':
        messages.error(request, "Нельзя редактировать проданный автомобиль.")
        return redirect('car_detail', vin=vin)

    if request.method == 'POST':
        form = CarEditForm(request.POST, instance=car)
        if form.is_valid():
            try:
                # save(commit=False) создает объект, но не пишет в базу
                updated_car = form.save(commit=False)

                # full_clean() запускает проверки из models.py (clean):
                # 1. Скидка <= 50
                # 2. Итоговая цена >= 100 000
                updated_car.full_clean()

                updated_car.save()
                messages.success(request, "Данные автомобиля обновлены!")
                return redirect('car_detail', vin=car.vin)
            except ValidationError as e:
                # Если сработала валидация (например, большая скидка)
                if hasattr(e, 'message_dict'):
                    for field, errors in e.message_dict.items():
                        for error in errors:
                            messages.error(request, f"Ошибка в поле {field}: {error}")
                else:
                    form.add_error(None, e)
    else:
        form = CarEditForm(instance=car)

    return render(request, 'form_base.html', {'form': form, 'title': f'Редактирование: {car.make} {car.model}'})


# ==========================================
# 4. ПРОДАЖИ
# ==========================================

@login_required
def sale_list(request):
    """История продаж"""
    if request.user.employee_profile.rank not in ['Менеджер', 'Продавец-консультант', 'Специалист по закупкам']:
        messages.error(request, "У вас нет доступа к продажам.")
        return redirect('dashboard')

    sales = Sale.objects.all().order_by('-sale_date')
    return render(request, 'sale_list.html', {'sales': sales})


@login_required
def sale_detail(request, sale_id):
    """Детальная карточка сделки"""
    # Проверка прав (доступно Менеджерам, Продавцам и Закупщикам для отчетности)
    if request.user.employee_profile.rank not in ['Менеджер', 'Продавец-консультант', 'Специалист по закупкам']:
        messages.error(request, "У вас нет доступа к просмотру этой продажи.")
        return redirect('dashboard')

    sale = get_object_or_404(Sale, pk=sale_id)

    # Получаем купленную машину (через таблицу Sale_list)
    sale_item = Sale_list.objects.filter(id_sale=sale).first()

    return render(request, 'detail_sale.html', {'sale': sale, 'item': sale_item})


@login_required
def create_sale(request):
    employee = request.user.employee_profile
    if employee.rank not in ['Менеджер', 'Продавец-консультант']:
        return redirect('dashboard')

    if request.method == 'POST':
        form = SaleForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    car = form.cleaned_data['vin']
                    client = form.cleaned_data['passport_client']
                    manual_price = form.cleaned_data['end_price']

                    # 1. Создаем продажу
                    sale = Sale.objects.create(
                        ip_employee=employee,
                        passport_client=client,
                        end_price=0
                    )

                    # 2. Цена (Ручная или Автоматическая)
                    if manual_price:
                        final_price = manual_price
                    else:
                        if car.discount > 0:
                            final_price = int(car.price * (1 - car.discount / 100))
                        else:
                            final_price = car.price

                    # 3. Состав продажи
                    Sale_list.objects.create(
                        id_sale=sale,
                        vin=car,
                        discounted_prise=final_price
                    )

                    # 4. Обновляем статус машины
                    car.car_status = 'Продан'
                    car.save()

                    # 5. Обновляем цену в чеке
                    if sale.end_price == 0:
                        sale.end_price = final_price
                        sale.save()

                messages.success(request, "✅ Продажа успешно оформлена!")
                return redirect('sale_list')  # Перенаправляем в список продаж

            except ValidationError as e:
                messages.error(request, f"Ошибка валидации: {e.message}")
            except Exception as e:
                messages.error(request, f"Системная ошибка: {e}")
    else:
        form = SaleForm()

    return render(request, 'form_base.html', {'form': form, 'title': 'Оформление продажи'})


# ==========================================
# 5. ТЕСТ-ДРАЙВЫ
# ==========================================

@login_required
def test_drive_list(request):
    tds = Test_drive.objects.all().order_by('-datetime_reservation')
    return render(request, 'test_drive_list.html', {'tds': tds})


@login_required
def edit_test_drive(request, td_id):
    td = get_object_or_404(Test_drive, pk=td_id)

    if request.method == 'POST':
        form = TestDriveEditForm(request.POST, instance=td)
        if form.is_valid():
            try:
                td = form.save(commit=False)
                td.full_clean()  # Проверка правил (дата за 2 дня и т.д.)
                td.save()
                messages.success(request, "Тест-драйв обновлен.")
                return redirect('test_drive_detail', td_id=td.pk)
            except ValidationError as e:
                messages.error(request, f"Ошибка валидации: {e}")
    else:
        form = TestDriveEditForm(instance=td)

    return render(request, 'form_base.html', {'form': form, 'title': f'Редактирование: Тест-драйв #{td.pk}'})


@login_required
def test_drive_detail(request, td_id):
    """Карточка тест-драйва"""
    td = get_object_or_404(Test_drive, pk=td_id)
    return render(request, 'detail_test_drive.html', {'td': td})


@login_required
def create_test_drive(request):
    employee = request.user.employee_profile

    if request.method == 'POST':
        form = TestDriveForm(request.POST)
        if form.is_valid():
            td = form.save(commit=False)
            td.id_employee = employee
            try:
                td.full_clean()
                td.save()
                messages.success(request, "✅ Клиент записан на тест-драйв!")
                return redirect('test_drive_list')
            except ValidationError as e:
                if hasattr(e, 'message_dict'):
                    for field, errors in e.message_dict.items():
                        for error in errors:
                            messages.error(request, f"{error}")
                else:
                    form.add_error(None, e)
    else:
        form = TestDriveForm()

    return render(request, 'form_base.html', {'form': form, 'title': 'Запись на тест-драйв'})


# ==========================================
# 6. УПРАВЛЕНИЕ ПЕРСОНАЛОМ
# ==========================================

@login_required
def employee_list(request):
    if request.user.employee_profile.rank != 'Менеджер':
        return redirect('dashboard')

    employees = Employee.objects.all().order_by('-employed', 'fio')
    return render(request, 'employee_list.html', {'employees': employees})


@login_required
def add_employee(request):
    """Добавление нового сотрудника + создание User для входа"""
    if request.user.employee_profile.rank != 'Менеджер':
        return redirect('dashboard')

    if request.method == 'POST':
        form = EmployeeForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # 1. Создаем сотрудника
                    emp = form.save(commit=False)
                    emp.employed = 1
                    emp.save()

                    # 2. Создаем пользователя Django (Логин: user_ID, Пароль: 1)
                    username = f"user_{emp.pk}"
                    user = User.objects.create_user(username=username, password='1')

                    # 3. Связываем
                    emp.user = user
                    emp.save()

                messages.success(request, f"Сотрудник {emp.fio} добавлен! Пароль для входа: 1")
                return redirect('employee_list')
            except Exception as e:
                messages.error(request, f"Ошибка при создании: {e}")
    else:
        form = EmployeeForm()

    return render(request, 'form_base.html', {'form': form, 'title': 'Новый сотрудник'})

@login_required
def fire_employee(request, emp_id):
    if request.user.employee_profile.rank != 'Менеджер':
        return redirect('dashboard')

    target_employee = get_object_or_404(Employee, pk=emp_id)

    future_tasks = Test_drive.objects.filter(
        id_employee=target_employee,
        result='Ожидается'
    )

    if request.method == 'POST':
        form = ReassignTestDriveForm(request.POST)

        if future_tasks.count() > 0:
            if form.is_valid():
                new_emp = form.cleaned_data['new_employee']
                updated_count = future_tasks.update(id_employee=new_emp)
                messages.info(request, f"Передано дел: {updated_count} сотруднику {new_emp.fio}")

                target_employee.employed = 0
                target_employee.save()
                messages.success(request, f"Сотрудник {target_employee.fio} уволен.")
                return redirect('employee_list')
        else:
            target_employee.employed = 0
            target_employee.save()
            messages.success(request, f"Сотрудник {target_employee.fio} уволен (активных дел не было).")
            return redirect('employee_list')

    else:
        form = ReassignTestDriveForm()

    return render(request, 'fire_employee.html', {
        'form': form,
        'target': target_employee,
        'count': future_tasks.count()
    })


# ==========================================
# КЛИЕНТЫ (Листинг, Добавление, Удаление)
# ==========================================

@login_required
def client_list(request):
    """Список клиентов с поиском"""
    clients = Client.objects.all().order_by('fio')

    # Простой поиск
    search = request.GET.get('search')
    if search:
        clients = clients.filter(Q(fio__icontains=search) | Q(passport_client__icontains=search))

    return render(request, 'client_list.html', {'clients': clients})


@login_required
def add_client(request):
    if request.method == 'POST':
        form = ClientForm(request.POST)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, "Клиент успешно добавлен!")
                return redirect('client_list')
            except Exception as e:
                messages.error(request, f"Ошибка БД: {e}")
    else:
        form = ClientForm()
    return render(request, 'form_base.html', {'form': form, 'title': 'Новый клиент'})


@login_required
def delete_client(request, passport_id):
    """Удаление клиента (только если нет покупок/тест-драйвов)"""
    client = get_object_or_404(Client, pk=passport_id)

    if request.method == 'POST':
        try:
            client.delete()
            messages.success(request, f"Клиент {client.fio} удален.")
        except Exception as e:
            messages.error(request, "Нельзя удалить клиента, у которого есть история покупок или тест-драйвов.")

    return redirect('client_list')