from my_db.models import Nomenclature, Price, Consumable, Operation, Combination


def duplicate_nomenclature(nomenclature_id):
    original = Nomenclature.objects.get(id=nomenclature_id)

    data = original.__dict__.copy()
    data.pop('id')
    data.pop('_state', None)

    duplicate = Nomenclature.objects.create(**data)

    Price.objects.bulk_create([
        Price(
            nomenclature=duplicate,
            title=price.title,
            price=price.price,
        )
        for price in original.prices.all()
    ])

    Consumable.objects.bulk_create([
        Consumable(
            nomenclature=duplicate,
            material_nomenclature=cons.material_nomenclature,
            consumption=cons.consumption,
            unit=cons.unit
        )
        for cons in original.consumables.all()
    ])

    combinations = original.combinations.prefetch_related('operations').all()
    for combination in combinations:
        new_operations = []
        for op in combination.operations.all():
            new_op = Operation.objects.create(
                title=op.title,
                time=op.time,
                price=op.price,
                equipment=op.equipment,
                rank=op.rank,
                nomenclature=duplicate
            )
            new_operations.append(new_op)

        new_combination = Combination.objects.create(
            nomenclature=duplicate,
            title=combination.title,
            status=combination.status,
        )

        new_combination.operations.set(new_operations)

    return duplicate