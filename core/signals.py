from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import Sale_list, Car, Sale, Order


# Правило: Когда автомобиль попадает в "Состав_Продажи", статус -> "продан"
@receiver(post_save, sender=Sale_list)
def car_sold_trigger(sender, instance, created, **kwargs):
    if created:
        car = instance.vin
        car.car_status = 'продан'
        car.save()

        # Правило: Если в продаже > 1 авто, считается общая сумма (тут обновление родительской Продажи)
        # Так как у нас связь 1:1 в таблице Состав, мы просто обновляем сумму
        sale = instance.id_sale
        sale.end_price = instance.discounted_prise
        sale.save()


# Правило: Расчет цены со скидкой при создании записи в Составе Продажи
@receiver(pre_save, sender=Sale_list)
def calculate_discount_price(sender, instance, **kwargs):
    car = instance.vin
    # Правило: Если есть скидка, применяется она
    if car.discount and car.discount > 0:
        price = car.price * (1 - car.discount / 100)
    else:
        price = car.price
    instance.discounted_prise = int(price)

# Правило: После получения авто (приход на склад) они добавляются в список.
# Реализуем как: Если у авто меняется статус на "прибыл", он готов к продаже.
# Это скорее процесс, чем триггер кода, но можно добавить логику здесь, если нужно.