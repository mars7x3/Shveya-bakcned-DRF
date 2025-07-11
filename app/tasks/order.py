from django.db import transaction
from django.db.models import Sum

from main_conf.celery import app
from my_db.enums import QuantityStatus, CombinationStatus, NomStatus
from my_db.models import NomCount, Nomenclature, QuantityHistory, QuantityNomenclature, Quantity, StaffProfile, Order, \
    Consumable, WorkDetail


@app.task
def gp_move_in_warehouse(order_id, staff_id):
    order = Order.objects.get(id=order_id)
    staff = StaffProfile.objects.get(id=staff_id)

    data = []

    for product in order.products.all():
        amount = WorkDetail.objects.filter(
            combination__status=CombinationStatus.DONE,
            work__party__nomenclature=product.nomenclature
        ).aggregate(total=Sum('amount'))['total'] or 0

        data.append({
            "product_id": product.nomenclature.id,
            "amount": amount,
            "price": product.true_price,
        })

    quantity = Quantity.objects.create(in_warehouse=order.in_warehouse, status=QuantityStatus.ACTIVE)

    create_data = []
    for i in data:
        create_data.append(
            QuantityNomenclature(
                quantity=quantity,
                nomenclature_id=i['product_id'],
                amount=i['amount'],
                price=i['price'],
            )
        )
    QuantityNomenclature.objects.bulk_create(create_data)

    QuantityHistory.objects.create(quantity=quantity, staff_id=staff.id, staff_name=staff.name,
                                   staff_surname=staff.surname, status=quantity.status)

    with transaction.atomic():
        nom_count_updates = []
        nomenclature_updates = []

        for item in data:
            obj, created = NomCount.objects.get_or_create(
                warehouse=quantity.in_warehouse,
                nomenclature_id=item["product_id"]
            )
            if created:
                obj.amount = item['amount']
                obj.save()

            else:
                obj.amount += item["amount"]
            nom_count_updates.append(obj)

            nomenclature = Nomenclature.objects.get(id=item['product_id'])

            total_amount_before = NomCount.objects.filter(nomenclature_id=item['product_id']).aggregate(
                total_amount=Sum('amount')
            )['total_amount'] or 0
            if total_amount_before > 0:
                total_amount_before -= item['amount']
            total_cost_before = total_amount_before * nomenclature.cost_price

            total_amount_after = obj.amount
            total_cost_after = total_cost_before + (item['amount'] * item['price'])

            nomenclature.cost_price = total_cost_after / total_amount_after
            nomenclature_updates.append(nomenclature)

        NomCount.objects.bulk_update(nom_count_updates, ['amount'])
        Nomenclature.objects.bulk_update(nomenclature_updates, ['cost_price'])


@app.task
def material_move_out_warehouse(order_id, staff_id):
    staff = StaffProfile.objects.get(id=staff_id)
    order = Order.objects.get(id=order_id)
    out_warehouse = order.out_warehouse

    consumables = Consumable.objects.filter(
        nomenclature__products__order=order,
        material_nomenclature__status=NomStatus.SHOP
    ).select_related('material_nomenclature')

    with transaction.atomic():
        quantity = Quantity.objects.create(
            out_warehouse=out_warehouse,
            status=QuantityStatus.ORDER
        )
        QuantityHistory.objects.create(quantity=quantity, staff_id=staff.id, staff_name=staff.name,
                                       staff_surname=staff.surname, status=quantity.status)

        qn_objects = []

        for consumable in consumables:
            amount = (WorkDetail.objects.filter(
                work__party__in=order.parties.filter(
                    nomenclature=consumable.nomenclature),
                combination__status=CombinationStatus.DONE).aggregate(total=Sum('amount'))['total'] or 0)

            material_nomenclature = consumable.material_nomenclature
            if not material_nomenclature:
                continue

            nom_count = NomCount.objects.filter(
                warehouse=out_warehouse,
                nomenclature=material_nomenclature
            ).first()

            if nom_count:
                nom_count.amount -= consumable.consumption * amount
                nom_count.save()
                qn_objects.append(QuantityNomenclature(
                    quantity=quantity,
                    nomenclature=material_nomenclature,
                    amount=consumable.consumption
                ))

        QuantityNomenclature.objects.bulk_create(qn_objects)

