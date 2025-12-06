from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Sale_list


@receiver(post_save, sender=Sale_list)
def car_sold_handler(sender, instance, created, **kwargs):
    """
    1. Меняем статус авто на 'Продан'.
    2. Обновляем итоговую сумму (End Price) в главной таблице Sale.
    """
    if created:
        # Меняем статус машины
        car = instance.vin
        car.car_status = 'Продан'
        car.save()

        # Обновляем сумму сделки в "шапке" (Sale)
        # Берем цену, которая была сохранена в Sale_list (введенная вручную или посчитанная)
        sale = instance.id_sale
        sale.end_price = instance.discounted_prise
        sale.save()