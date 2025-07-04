from main_conf.celery import app
from my_db.models import Warehouse, NomCount


@app.task
def write_off_from_warehouse(staff, consumables):
    warehouse = Warehouse.objects.filter(staffs=staff).first()

    update_list = []
    for c in consumables:
        nom_count = c.nomenclature.counts.filter(warehouse=warehouse).first()
        nom_count.amount = c.remainder
        update_list.append(nom_count)

    NomCount.objects.bulk_update(nom_count, ['amount'])


