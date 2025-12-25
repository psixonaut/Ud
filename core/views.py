from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.db.models import Sum, Count, Case, When, Value, IntegerField, Q
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.forms import formset_factory
from .models import *
from .forms import *


# ==========================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ==========================================

def auto_complete_test_drives():
    now = timezone.now()
    updated_count = Test_drive.objects.filter(
        result='Ожидается',
        datetime_reservation__lt=now
    ).update(result='Проведён')

    return updated_count


# ==========================================
# 1. АВТОРИЗАЦИЯ И ГЛАВНАЯ
# ==========================================

def custom_login(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            fio = form.cleaned_data['fio'].strip()
            password = form.cleaned_data['password']
            try:
                employee = Employee.objects.get(fio__iexact=fio)

                if employee.employed == 0:
                    messages.error(request, "Доступ запрещен: Сотрудник уволен.")
                    return render(request, 'login.html', {'form': form})

                if employee.user:
                    user = authenticate(username=employee.user.username, password=password)
                    if user:
                        login(request, user)
                        return redirect('dashboard')

                messages.error(request, "Ошибка входа: Неверный пароль или пользователь не настроен.")
            except Employee.DoesNotExist:
                messages.error(request, "Ошибка: Сотрудник с таким ФИО не найден.")
    else:
        form = LoginForm()
    return render(request, 'login.html', {'form': form})


def user_logout(request):
    logout(request)
    return redirect('login')


# ==========================================
# ЛОГИКА ДОБАВЛЕНИЯ КЛИЕНТА С ВОЗВРАТОМ
# ==========================================

@login_required
def add_client(request):
    if request.method == 'POST':
        form = ClientForm(request.POST)
        if form.is_valid():
            try:
                client = form.save()
                messages.success(request, f"Клиент {client.fio} добавлен.")
                next_url = request.GET.get('next')
                if next_url:
                    return redirect(f"{next_url}?new_client={client.pk}")

                return redirect('client_list')
            except Exception as e:
                messages.error(request, f"Ошибка: {e}")
    else:
        form = ClientForm()

    return render(request, 'form_base.html', {'form': form, 'title': 'Новый клиент'})


@login_required
def dashboard(request):
    try:
        employee = request.user.employee_profile
    except:
        messages.error(request, "Ошибка профиля: Не связан с сотрудником.")
        return redirect('logout')
    auto_complete_test_drives()
    context = {'employee': employee}

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
    cars = Car.objects.exclude(car_status='Продан')
    form = CarFilterForm(request.GET)

    if form.is_valid():
        if form.cleaned_data['search']:
            search = form.cleaned_data['search']
            cars = cars.filter(Q(vin__icontains=search) | Q(make__icontains=search) | Q(model__icontains=search))

        if form.cleaned_data['status']:
            cars = cars.filter(car_status=form.cleaned_data['status'])
        if form.cleaned_data['price_min']:
            cars = cars.filter(price__gte=form.cleaned_data['price_min'])
        if form.cleaned_data['price_max']:
            cars = cars.filter(price__lte=form.cleaned_data['price_max'])
        if form.cleaned_data['year_min']:
            cars = cars.filter(make_year__gte=form.cleaned_data['year_min'])

        if form.cleaned_data['gearbox']:
            cars = cars.filter(gearbox__in=form.cleaned_data['gearbox'])
        if form.cleaned_data['driven_wheels']:
            cars = cars.filter(driven_wheels__in=form.cleaned_data['driven_wheels'])
        if form.cleaned_data['body']:
            cars = cars.filter(body__in=form.cleaned_data['body'])

        ordering = form.cleaned_data.get('ordering')

        if ordering == 'price_asc':
            cars = cars.order_by('price')
        elif ordering == 'price_desc':
            cars = cars.order_by('-price')
        elif ordering == 'year_desc':
            cars = cars.order_by('-make_year')
        else:
            cars = cars.annotate(
                status_order=Case(
                    When(car_status='В продаже', then=Value(1)),
                    When(car_status='Для тест-драйвов', then=Value(2)),
                    When(car_status='Прибыл', then=Value(3)),
                    When(car_status='В пути', then=Value(4)),
                    default=Value(5),
                    output_field=IntegerField(),
                )
            ).order_by('status_order', 'make', 'model')
    else:
        cars = cars.annotate(
            status_order=Case(
                When(car_status='В продаже', then=Value(1)),
                When(car_status='Для тест-драйвов', then=Value(2)),
                default=Value(3),
                output_field=IntegerField(),
            )
        ).order_by('status_order', 'make', 'model')

    return render(request, 'car_list.html', {'cars': cars, 'form': form})


@login_required
def car_detail(request, vin):
    car = get_object_or_404(Car, pk=vin)
    auto_complete_test_drives()

    history = Test_drive.objects.filter(vin=car).order_by('-datetime_reservation')
    return render(request, 'detail_car.html', {'car': car, 'history': history})


@login_required
def edit_car(request, vin):
    allowed_roles = ['Менеджер', 'Продавец-консультант', 'Специалист по закупкам']
    if request.user.employee_profile.rank not in allowed_roles:
        messages.error(request, "У вас нет прав на редактирование автомобилей.")
        return redirect('car_detail', vin=vin)

    car = get_object_or_404(Car, pk=vin)
    if car.car_status == 'Продан':
        messages.error(request, "Нельзя редактировать проданный автомобиль.")
        return redirect('car_detail', vin=vin)

    if request.method == 'POST':
        form = CarEditForm(request.POST, instance=car)
        if form.is_valid():
            try:
                updated_car = form.save(commit=False)
                updated_car.full_clean()
                updated_car.save()
                messages.success(request, "Данные автомобиля успешно обновлены.")
                return redirect('car_detail', vin=car.vin)
            except ValidationError as e:
                if hasattr(e, 'message_dict'):
                    for field, errors in e.message_dict.items():
                        for error in errors:
                            messages.error(request, f"Ошибка в поле '{field}': {error}")
                else:
                    messages.error(request, f"Ошибка валидации: {e}")
            except Exception as e:
                if "chk_Цена" in str(e):
                    messages.error(request, "Ошибка сохранения: Цена должна быть больше 100 000 руб.")
                elif "chk_Скидка" in str(e):
                    messages.error(request, "Ошибка сохранения: Скидка не может быть больше 50%.")
                else:
                    messages.error(request, f"Системная ошибка: {e}")
    else:
        form = CarEditForm(instance=car)

    return render(request, 'form_base.html', {'form': form, 'title': f'Редактирование: {car.make} {car.model}'})


# ==========================================
# 3. ЗАКУПКИ
# ==========================================

@login_required
def order_list(request):
    if request.user.employee_profile.rank != 'Специалист по закупкам':
        return redirect('dashboard')

    orders = Order.objects.all().order_by('-date_order')
    return render(request, 'order_list.html', {'orders': orders})


@login_required
def order_detail(request, order_id):
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
            messages.success(request, f"Заказ на {order.amount} авто успешно оформлен.")
            return redirect('order_list')
    else:
        form = OrderForm()
    return render(request, 'form_base.html', {'form': form, 'title': 'Создание заказа'})


@login_required
def accept_car(request, order_id):
    order = get_object_or_404(Order, pk=order_id)

    if order.state_order == 'Оформлен':
        return redirect('order_list')

    CarFormSet = formset_factory(CarArrivalForm, extra=order.amount)

    if request.method == 'POST':
        formset = CarFormSet(request.POST)
        if formset.is_valid():
            try:
                with transaction.atomic():
                    for form in formset:
                        Car.objects.create(
                            vin=form.cleaned_data['vin'],
                            color=form.cleaned_data['color'],
                            price=form.cleaned_data['price'],
                            date_of_delivery=timezone.now().date(),
                            car_status='В продаже',
                            make=order.make, model=order.model, engine=order.engine,
                            gearbox=order.gearbox, driven_wheels=order.driven_wheels,
                            body=order.body, make_year=order.make_year, trim=order.trim,
                            addons=order.addons
                        )

                    order.state_order = 'Оформлен'
                    order.save()

                messages.success(request, "Автомобили успешно приняты на склад.")
                return redirect('order_list')
            except Exception as e:
                messages.error(request, f"Ошибка при сохранении: {e}")
    else:
        formset = CarFormSet()

    return render(request, 'form_accept_mass.html', {'formset': formset, 'order': order, 'title': 'Приемка партии'})


# ==========================================
# 4. ПРОДАЖИ
# ==========================================

@login_required
def sale_list(request):
    if request.user.employee_profile.rank not in ['Менеджер', 'Специалист по закупкам']:
        messages.error(request, "У вас нет доступа к истории продаж.")
        return redirect('dashboard')

    sales = Sale.objects.all().order_by('-sale_date')

    form = SaleFilterForm(request.GET)

    if form.is_valid():
        if form.cleaned_data['search']:
            s = form.cleaned_data['search']
            sales = sales.filter(
                Q(sale_list__vin__make__icontains=s) |
                Q(sale_list__vin__model__icontains=s) |
                Q(sale_list__vin__vin__icontains=s) |
                Q(passport_client__fio__icontains=s) |
                Q(ip_employee__fio__icontains=s)
            )

        if form.cleaned_data['date_from']:
            sales = sales.filter(sale_date__gte=form.cleaned_data['date_from'])
        if form.cleaned_data['date_to']:
            sales = sales.filter(sale_date__lte=form.cleaned_data['date_to'])

        if form.cleaned_data['price_min']:
            sales = sales.filter(end_price__gte=form.cleaned_data['price_min'])
        if form.cleaned_data['price_max']:
            sales = sales.filter(end_price__lte=form.cleaned_data['price_max'])

    return render(request, 'sale_list.html', {'sales': sales, 'form': form})


@login_required
def sale_detail(request, sale_id):
    if request.user.employee_profile.rank not in ['Менеджер', 'Продавец-консультант', 'Специалист по закупкам']:
        return redirect('dashboard')
    sale = get_object_or_404(Sale, pk=sale_id)
    sale_item = Sale_list.objects.filter(id_sale=sale).first()
    return render(request, 'detail_sale.html', {'sale': sale, 'item': sale_item})


@login_required
def create_sale(request):
    employee = request.user.employee_profile
    if employee.rank not in ['Менеджер', 'Продавец-консультант']:
        return redirect('dashboard')

    initial_data = {}
    new_client_id = request.GET.get('new_client')
    if new_client_id:
        initial_data['passport_client'] = new_client_id

    if request.method == 'POST':
        form = SaleForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    car = form.cleaned_data['vin']
                    client = form.cleaned_data['passport_client']
                    manual_price = form.cleaned_data['end_price']

                    sale = Sale.objects.create(
                        ip_employee=employee,
                        passport_client=client,
                        end_price=0
                    )

                    if manual_price:
                        final_price = manual_price
                    else:
                        if car.discount > 0:
                            final_price = int(car.price * (1 - car.discount / 100))
                        else:
                            final_price = car.price

                    Sale_list.objects.create(id_sale=sale, vin=car, discounted_prise=final_price)

                    car.car_status = 'Продан'
                    car.save()

                    if sale.end_price == 0:
                        sale.end_price = final_price
                        sale.save()

                messages.success(request, "Продажа успешно оформлена.")
                return redirect('sale_list')

            except ValidationError as e:
                messages.error(request, f"Ошибка валидации: {e.message}")
            except Exception as e:
                messages.error(request, f"Системная ошибка: {e}")
    else:
        form = SaleForm(initial=initial_data)

    return render(request, 'form_with_client.html', {'form': form, 'title': 'Оформление продажи'})


@login_required
def reassign_car(request, car_vin):
    old_car = get_object_or_404(Car, pk=car_vin)
    future_tds = Test_drive.objects.filter(vin=old_car, result='Ожидается')

    if request.method == 'POST':
        form = CarReassignForm(request.POST)
        if form.is_valid():
            new_car = form.cleaned_data['new_car']
            future_tds.update(vin=new_car)
            messages.success(request,
                             f"Тест-драйвы ({future_tds.count()} шт.) перенесены на {new_car}. Теперь можно продавать.")
            return redirect('create_sale')
    else:
        form = CarReassignForm()

    return render(request, 'reassign_car.html', {'form': form, 'old_car': old_car, 'count': future_tds.count()})


# ==========================================
# 5. ТЕСТ-ДРАЙВЫ
# ==========================================

@login_required
def test_drive_list(request):
    auto_complete_test_drives()
    tds = Test_drive.objects.all().order_by('-datetime_reservation')
    return render(request, 'test_drive_list.html', {'tds': tds})


@login_required
def cancel_test_drive(request, td_id):
    td = get_object_or_404(Test_drive, pk=td_id)

    if td.result != 'Ожидается':
        messages.error(request, "Нельзя отменить уже завершенный тест-драйв.")
    else:
        td.result = 'Отказ'
        td.save()
        messages.success(request, "Тест-драйв отменен (переведен в статус 'Отказ').")

    return redirect('test_drive_detail', td_id=td.pk)


@login_required
def delete_test_drive(request, td_id):

    td = get_object_or_404(Test_drive, pk=td_id)

    if request.method == 'POST':
        try:
            td.delete()
            messages.success(request, "Запись о тест-драйве удалена.")
            return redirect('test_drive_list')
        except Exception as e:
            messages.error(request, f"Ошибка удаления: {e}")

    return redirect('test_drive_detail', td_id=td.pk)


@login_required
def test_drive_detail(request, td_id):
    td = get_object_or_404(Test_drive, pk=td_id)
    return render(request, 'detail_test_drive.html', {'td': td})


@login_required
def create_test_drive(request):
    employee = request.user.employee_profile

    # Проверка на нового клиента
    initial_data = {}
    new_client_id = request.GET.get('new_client')
    if new_client_id:
        initial_data['passport_client'] = new_client_id

    if request.method == 'POST':
        form = TestDriveForm(request.POST)
        if form.is_valid():
            td = form.save(commit=False)
            td.id_employee = employee
            try:
                td.full_clean()
                td.save()
                messages.success(request, "Клиент успешно записан на тест-драйв.")
                return redirect('test_drive_list')
            except ValidationError as e:
                if hasattr(e, 'message_dict'):
                    for field, errors in e.message_dict.items():
                        for error in errors:
                            messages.error(request, f"Ошибка в поле {field}: {error}")
                else:
                    form.add_error(None, e)
    else:
        form = TestDriveForm(initial=initial_data)
    return render(request, 'form_with_client.html', {'form': form, 'title': 'Запись на тест-драйв'})


@login_required
def edit_test_drive(request, td_id):
    td = get_object_or_404(Test_drive, pk=td_id)
    if td.result == 'Ожидается':
        FormClass = TestDriveEditForm
    else:
        FormClass = TestDriveResultOnlyForm

    if request.method == 'POST':
        form = FormClass(request.POST, instance=td)
        if form.is_valid():
            try:
                updated_td = form.save(commit=False)
                if td.result == 'Ожидается':
                    updated_td.full_clean()

                updated_td.save()
                messages.success(request, "Данные тест-драйва обновлены.")
                return redirect('test_drive_detail', td_id=td.pk)
            except ValidationError as e:
                messages.error(request, f"Ошибка валидации: {e}")
            except Exception as e:
                messages.error(request, f"Ошибка: {e}")
    else:
        form = FormClass(instance=td)

    return render(request, 'form_base.html', {
        'form': form,
        'title': f'Редактирование: Тест-драйв #{td.pk}'
    })


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
    if request.user.employee_profile.rank != 'Менеджер': return redirect('dashboard')

    if request.method == 'POST':
        form = EmployeeForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    emp = form.save(commit=False)
                    emp.employed = 1
                    emp.save()

                    username = f"user_{emp.pk}"
                    user = User.objects.create_user(username=username, password=form.cleaned_data['password'])

                    emp.user = user
                    emp.save()

                messages.success(request, f"Сотрудник {emp.fio} успешно добавлен.")
                return redirect('employee_list')
            except Exception as e:
                messages.error(request, f"Ошибка: {e}")
    else:
        form = EmployeeForm()

    return render(request, 'form_base.html', {'form': form, 'title': 'Новый сотрудник'})


@login_required
def edit_employee(request, emp_id):
    if request.user.employee_profile.rank != 'Менеджер': return redirect('dashboard')

    employee = get_object_or_404(Employee, pk=emp_id)

    if request.method == 'POST':
        form = EmployeeEditForm(request.POST, instance=employee)
        if form.is_valid():
            try:
                new_pass = form.cleaned_data['new_password']
                if employee.user and new_pass:
                    employee.user.set_password(new_pass)
                    employee.user.save()
                    messages.success(request, f"Пароль для {employee.fio} изменен.")
                return redirect('employee_list')
            except Exception as e:
                messages.error(request, f"Ошибка: {e}")
    else:
        form = EmployeeEditForm(instance=employee)

    return render(request, 'form_base.html', {'form': form, 'title': f'Смена пароля: {employee.fio}'})


@login_required
def fire_employee(request, emp_id):
    if request.user.employee_profile.rank != 'Менеджер': return redirect('dashboard')

    target = get_object_or_404(Employee, pk=emp_id)
    future = Test_drive.objects.filter(id_employee=target, result='Ожидается')

    if request.method == 'POST':
        form = ReassignTestDriveForm(request.POST)

        if future.count() > 0:
            if form.is_valid():
                new_emp = form.cleaned_data['new_employee']
                future.update(id_employee=new_emp)

                target.employed = 0
                target.save()
                messages.success(request, f"Сотрудник {target.fio} уволен, дела переданы.")
                return redirect('employee_list')
        else:
            target.employed = 0
            target.save()
            messages.success(request, f"Сотрудник {target.fio} уволен.")
            return redirect('employee_list')

    else:
        form = ReassignTestDriveForm()

    return render(request, 'fire_employee.html', {'form': form, 'target': target, 'count': future.count()})


# ==========================================
# 7. КЛИЕНТЫ
# ==========================================

@login_required
def client_list(request):
    clients = Client.objects.all().order_by('fio')

    search = request.GET.get('search')
    if search:
        clients = clients.filter(Q(fio__icontains=search) | Q(passport_client__icontains=search))

    return render(request, 'client_list.html', {'clients': clients})


@login_required
def add_client(request):
    next_url = request.POST.get('next') or request.GET.get('next')

    if request.method == 'POST':
        form = ClientForm(request.POST)
        if form.is_valid():
            try:
                client = form.save()
                messages.success(request, f"Клиент {client.fio} успешно добавлен.")
                if next_url:
                    return redirect(f"{next_url}?new_client={client.pk}")
                return redirect('client_list')
            except Exception as e:
                messages.error(request, f"Ошибка: {e}")
    else:
        form = ClientForm()
    return render(request, 'form_base.html', {
        'form': form,
        'title': 'Новый клиент',
        'next_url': next_url
    })


@login_required
def delete_client(request, passport_id):
    client = get_object_or_404(Client, pk=passport_id)
    if request.method == 'POST':
        try:
            client.delete()
            messages.success(request, "Клиент удален.")
        except:
            messages.error(request, "Нельзя удалить клиента, у которого есть история покупок или тест-драйвов.")
    return redirect('client_list')