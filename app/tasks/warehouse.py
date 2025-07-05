from main_conf.celery import app
from my_db.models import Warehouse, NomCount, PartyConsumable


@app.task
def write_off_from_warehouse(staff_id, consumables__ids):
    warehouse = Warehouse.objects.filter(staffs__id=staff_id).first()
    consumables = PartyConsumable.objects.filter(id__in=consumables__ids)

    update_list = []
    for c in consumables:
        nom_count = c.nomenclature.counts.filter(warehouse=warehouse).first()
        nom_count.amount = c.remainder if c.remainder else 0
        update_list.append(nom_count)

    NomCount.objects.bulk_update(update_list, ['amount'])


