from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import Sale_list


@receiver(post_save, sender=Sale_list)
def car_sold_handler(sender, instance, created, **kwargs):
    """
    1. Меняем статус авто на 'Продан'.
    2. Если пользователь не ввел свою цену (end_price == 0), берем цену из состава продажи.
    """
    if created:
        # Меняем статус машины
        car = instance.vin
        car.car_status = 'Продан'
        car.save()

        # Работаем с ценой продажи
        sale = instance.id_sale

        # ЛОГИКА ПРИОРИТЕТА:
        # Если в "шапке" (Sale) цена равна 0 (пользователь ничего не ввел или оставил дефолт),
        # то мы записываем туда цену машины (discounted_prise).
        # Если пользователь ввел что-то свое (например, 400 000 000), то sale.end_price будет > 0,
        # и мы НЕ будем его трогать.
        if sale.end_price == 0:
            sale.end_price = instance.discounted_prise
            sale.save()


@receiver(pre_save, sender=Sale_list)
def calculate_discount_price(sender, instance, **kwargs):
    # Эта часть не меняется, она уже перенесена в метод clean() модели,
    # но можно оставить здесь для подстраховки, если clean() будет обойден.
    # Но основная логика у нас сейчас в models.py -> clean()
    pass