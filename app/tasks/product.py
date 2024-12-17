from celery import shared_task
from django.db.models import Sum, F
from my_db.models import Nomenclature, Operation, Consumable, NomType
from django.utils import timezone
from decimal import Decimal

@shared_task
def change_product_cost_price():
    """
    Обновляет себестоимость (cost_price) для готовых продуктов.
    """
    products = Nomenclature.objects.filter(type=NomType.GP)
    update_list = []
    for product in products:
        total_cost = Decimal(0)

        operations = Operation.objects.filter(nomenclature=product, is_active=True)

        for operation in operations:
            consumables = Consumable.objects.filter(operation_nom__operation=operation)

            materials_cost = consumables.aggregate(
                total_material_cost=Sum(
                    (F('consumption') + F('waste')) * F('operation_nom__nomenclature__cost_price')
                )
            )['total_material_cost'] or 0

            total_cost += operation.price + Decimal(materials_cost)

        product.cost_price = total_cost
        update_list.append(product)

    Nomenclature.objects.bulk_update(update_list, ['cost_price'])
    print(f"[{timezone.now()}] Cost prices for finished products updated successfully.")