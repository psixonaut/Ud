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

        if sale.end_price == 0:
            sale.end_price = instance.discounted_prise
            sale.save()


@receiver(pre_save, sender=Sale_list)
def calculate_discount_price(sender, instance, **kwargs):
    pass