from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import Sale_list


@receiver(post_save, sender=Sale_list)
def car_sold_handler(sender, instance, created, **kwargs):
    if created:
        car = instance.vin
        car.car_status = 'Продан'
        car.save()

        sale = instance.id_sale
        sale.end_price = instance.discounted_prise
        sale.save()


@receiver(pre_save, sender=Sale_list)
def calculate_discount_price(sender, instance, **kwargs):
    car = instance.vin
    if car.discount and car.discount > 0:
        price = car.price * (1 - car.discount / 100)
    else:
        price = car.price
    instance.discounted_prise = int(price)