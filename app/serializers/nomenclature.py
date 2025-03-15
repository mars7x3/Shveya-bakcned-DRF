from django.db import transaction
from rest_framework import serializers

from my_db.enums import NomType
from my_db.models import Nomenclature, Pattern, Operation, Combination, Rank, Equipment, Consumable, Size, \
    EquipmentImages, EquipmentService, StaffProfile, CombinationFile, Price


class GPListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Nomenclature
        fields = ['id', 'vendor_code', 'is_active', 'title', 'cost_price']


class MaterialListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Nomenclature
        fields = ['id', 'vendor_code', 'title']


class PatternSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pattern
        fields = ['id', 'image']


class EquipmentImagesSerializer(serializers.ModelSerializer):
    class Meta:
        model = EquipmentImages
        fields = ['id', 'image']


class EquipmentServiceStaffSerializer(serializers.ModelSerializer):
    class Meta:
        model = StaffProfile
        fields = ['id', 'name', 'surname']


class EquipmentServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = EquipmentService
        fields = ['id', 'equipment', 'staff', 'text', 'price', 'created_at']
        extra_kwargs = {'equipment': {'write_only': True, 'required': True}}


class EquipmentServiceReadSerializer(EquipmentServiceSerializer):
    staff = EquipmentServiceStaffSerializer()


class EquipmentSerializer(serializers.ModelSerializer):
    images = EquipmentImagesSerializer(many=True)
    services = EquipmentServiceReadSerializer(many=True)

    class Meta:
        model = Equipment
        fields = '__all__'


class EquipmentCRUDSerializer(serializers.ModelSerializer):
    class Meta:
        model = Equipment
        fields = '__all__'


class EquipmentListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Equipment
        fields = ['id', 'title', 'price', 'is_active']


class EquipmentImageCRUDSerializer(serializers.Serializer):
    equipment_id = serializers.IntegerField(help_text="ID оборудования, к которому добавляются изображения.")
    images = serializers.ListField(
        child=serializers.ImageField(),
        required=False,
        help_text="Список файлов изображений для добавления к оборудованию."
    )
    delete_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        help_text="Список ID изображений для удаления. PS: в свагере не работает это место, "
                  "но если отправишь [1, 2], то сработает"
    )


class CombinationOperationsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Operation
        fields = ['id', 'title']


class NomenclatureSerializer(serializers.ModelSerializer):
    class Meta:
        model = Nomenclature
        fields = ['id', 'title', 'unit']


class EquipmentReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Equipment
        fields = ['id', 'title']


class OperationSerializer(serializers.ModelSerializer):
    nomenclature = NomenclatureSerializer(read_only=True)
    equipment = EquipmentReadSerializer(read_only=True)

    class Meta:
        model = Operation
        fields = ['id', 'title', 'price', 'time', 'nomenclature', 'equipment', 'rank', 'is_active']


class CombinationSerializer(serializers.ModelSerializer):
    operations = OperationSerializer(many=True)

    class Meta:
        model = Combination
        fields = '__all__'


class CombinationCRUDSerializer(CombinationSerializer):
    operations = serializers.PrimaryKeyRelatedField(
        queryset=Operation.objects.all(),
        required=False,
        many=True
    )

    def create(self, validated_data):
        operations_data = validated_data.pop('operations', [])
        combination = super().create(validated_data)
        if operations_data:
            combination.operations.set(operations_data)
        return combination

    def update(self, instance, validated_data):
        operations_data = validated_data.pop('operations', None)
        combination = super().update(instance, validated_data)

        if operations_data is not None:
            current_operations = set(combination.operations.values_list('id', flat=True))
            new_operations = set(operations_data)

            to_add = new_operations - current_operations
            to_remove = current_operations - new_operations

            if to_remove:
                combination.operations.remove(*to_remove)
            if to_add:
                combination.operations.add(*to_add)

        return combination


class ColorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Nomenclature
        fields = ['id', 'title']


class ConsumableSerializer(serializers.ModelSerializer):
    color = ColorSerializer(read_only=True)
    material_nomenclature = NomenclatureSerializer(read_only=True)

    class Meta:
        model = Consumable
        fields = ['id', 'material_nomenclature', 'color', 'consumption']


class ConsumableCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Consumable
        fields = ['material_nomenclature', 'color', 'consumption']


class OperationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Operation
        fields = ['id', 'title', 'price', 'time', 'equipment', 'rank', 'is_active']


class PriceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Price
        fields = ['title', 'price']


class GPDetailSerializer(serializers.ModelSerializer):
    combinations = CombinationSerializer(read_only=True, many=True)
    nom_operations = OperationSerializer(read_only=True, many=True)
    consumables = ConsumableSerializer(read_only=True, many=True)
    prices = PriceSerializer(read_only=True, many=True)

    class Meta:
        model = Nomenclature
        fields = ['id', 'vendor_code', 'cost_price', 'is_active', 'title', 'image',
                  'prices', 'combinations', 'nom_operations', 'consumables']


class CombinationCreateSerializer(serializers.ModelSerializer):
    operations = OperationCreateSerializer(required=False, many=True)

    class Meta:
        model = Combination
        fields = ['id', 'operations', 'title']


class GPCRUDSerializer(serializers.ModelSerializer):
    prices = PriceSerializer(required=False, many=True)
    operations = OperationCreateSerializer(required=False, many=True)
    consumables = ConsumableCreateSerializer(required=False, many=True)
    combinations =  CombinationCreateSerializer(required=False, many=True)

    class Meta:
        model = Nomenclature
        fields = ['id', 'vendor_code', 'is_active', 'title', 'cost_price', 'image',
                  'prices', 'operations', 'consumables', 'combinations']

    def validate(self, attrs):
        attrs['type'] = NomType.GP
        return attrs

    def create(self, validated_data):
        prices_data = validated_data.pop('prices', [])
        consumables_data = validated_data.pop('consumables', [])
        operations_data = validated_data.pop('operations', [])
        combinations_data = validated_data.pop('combinations', [])

        nomenclature = Nomenclature.objects.create(**validated_data)

        Price.objects.bulk_create([Price(nomenclature=nomenclature, **data) for data in prices_data])
        Consumable.objects.bulk_create([Consumable(nomenclature=nomenclature, **data) for data in consumables_data])
        Operation.objects.bulk_create([Operation(nomenclature=nomenclature, **data) for data in operations_data])

        for data in combinations_data:
            c_operations_data = data.pop('operations')
            create_data = [Operation(nomenclature=nomenclature, **data) for data in c_operations_data]
            c_operations = Operation.objects.bulk_create(create_data)
            operations_ids = [op.id for op in c_operations]

            combination = Combination.objects.create(nomenclature=nomenclature, **data)
            combination.operations.set(operations_ids)

        operation_data_by_title = {}
        for data in operations_data:
            title = data['title']
            if title not in operation_data_by_title:
                operation_data_by_title[title] = data.copy()

        existing_samples = set(
            Operation.objects.filter(title__in=operation_data_by_title.keys(), is_sample=True)
            .values_list('title', flat=True)
        )

        sample_operations = [
            Operation(is_sample=True, **data)
            for title, data in operation_data_by_title.items() if title not in existing_samples
        ]
        if sample_operations:
            Operation.objects.bulk_create(sample_operations)

        return nomenclature

    def update(self, instance, validated_data):
        prices_data = validated_data.pop('prices', [])
        consumables_data = validated_data.pop('consumables', [])
        operations_data = validated_data.pop('operations', [])
        combinations_data = validated_data.pop('combinations', [])

        nomenclature = super().update(instance, validated_data)

        with transaction.atomic():
            nomenclature.prices.all().delete()
            nomenclature.combinations.all().delete()
            nomenclature.operations.all().delete()
            nomenclature.consumables.all().delete()

        Price.objects.bulk_create([Price(nomenclature=nomenclature, **data) for data in prices_data])
        Consumable.objects.bulk_create([Consumable(nomenclature=nomenclature, **data) for data in consumables_data])
        Operation.objects.bulk_create([Operation(nomenclature=nomenclature, **data) for data in operations_data])

        for data in combinations_data:
            c_operations_data = data.pop('operations')
            create_data = [Operation(nomenclature=nomenclature, **data) for data in c_operations_data]
            c_operations = Operation.objects.bulk_create(create_data)
            operations_ids = [op.id for op in c_operations]

            combination = Combination.objects.create(nomenclature=nomenclature, **data)
            combination.operations.set(operations_ids)
            combination.save()

        operation_data_by_title = {}
        for data in operations_data:
            title = data['title']
            if title not in operation_data_by_title:
                operation_data_by_title[title] = data.copy()

        existing_samples = set(
            Operation.objects.filter(title__in=operation_data_by_title.keys(), is_sample=True)
            .values_list('title', flat=True)
        )

        sample_operations = [
            Operation(is_sample=True, **data)
            for title, data in operation_data_by_title.items() if title not in existing_samples
        ]
        if sample_operations:
            Operation.objects.bulk_create(sample_operations)

        return nomenclature


class PatternCRUDSerializer(serializers.Serializer):
    product_id = serializers.IntegerField(help_text="ID продукта, к которому добавляются изображения.")
    images = serializers.ListField(
        child=serializers.ImageField(),
        required=False,
        help_text="Список файлов изображений для добавления к продукту."
    )
    delete_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        help_text="Список ID изображений для удаления. PS: в свагере не работает это место, "
                  "но если отправишь [1, 2], то сработает"
    )


class ConsumableCRUDSerializer(serializers.ModelSerializer):
    class Meta:
        model = Consumable
        fields = ['size', 'consumption']


class OperationRankSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rank
        fields = ['id', 'title']


class OperationNomenclatureSerializer(serializers.ModelSerializer):
    class Meta:
        model = Nomenclature
        fields = ['id', 'vendor_code', 'title']


class OperationCRUDSerializer(serializers.ModelSerializer):
    class Meta:
        model = Operation
        fields = ['id', 'title', 'time', 'price', 'nomenclature', 'equipment', 'rank', 'is_active', 'is_sample']


class OperationEquipmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Equipment
        fields = ['id', 'title']


class OperationRetrieveSerializer(serializers.ModelSerializer):
    nomenclature = OperationNomenclatureSerializer(read_only=True)
    rank = OperationRankSerializer(read_only=True)
    equipment = OperationEquipmentSerializer(read_only=True)

    class Meta:
        model = Operation
        fields = ['id', 'title', 'time', 'price', 'nomenclature', 'equipment', 'rank', 'is_active']


class ProductListSerializer(serializers.ModelSerializer):
    time = serializers.SerializerMethodField()

    class Meta:
        model = Nomenclature
        fields = ['id', 'vendor_code', 'title', 'cost_price', 'time']

    def get_time(self, obj):
        # Суммируем время всех связанных операций
        return sum(operation.time for operation in obj.operations.all())



