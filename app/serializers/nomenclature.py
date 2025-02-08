from rest_framework import serializers

from my_db.enums import NomType
from my_db.models import Nomenclature, Pattern, Operation, Combination, Rank, Equipment, Consumable, Size, \
     EquipmentImages, EquipmentService, StaffProfile


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


class CombinationSerializer(serializers.ModelSerializer):
    operations = CombinationOperationsSerializer(many=True)

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


class NomenclatureSerializer(serializers.ModelSerializer):
    class Meta:
        model = Nomenclature
        fields = ['id', 'title', 'unit']


class Size2Serializer(serializers.ModelSerializer):
    class Meta:
        model = Size
        fields = ['id', 'title']


class ConsumableSerializer(serializers.ModelSerializer):
    size = Size2Serializer()

    class Meta:
        model = Consumable
        fields = ['id', 'size', 'consumption']


class OperationSerializer(serializers.ModelSerializer):

    class Meta:
        model = Operation
        fields = ['id', 'title', 'price', 'time', 'nomenclature', 'equipment', 'rank', 'is_active']


class GPDetailSerializer(serializers.ModelSerializer):
    combinations = CombinationSerializer(read_only=True, many=True)
    operations = OperationSerializer(read_only=True, many=True)
    consumables = ConsumableSerializer(read_only=True, many=True)

    class Meta:
        model = Nomenclature
        fields = ['id', 'vendor_code', 'is_active', 'title', 'combinations', 'operations', 'consumables']


class GPCRUDSerializer(serializers.ModelSerializer):
    class Meta:
        model = Nomenclature
        fields = ['id', 'vendor_code', 'is_active', 'title']

    def validate(self, attrs):
        attrs['type'] = NomType.GP
        return attrs


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


class OperationCRUDSerializer(serializers.ModelSerializer):
    class Meta:
        model = Operation
        fields = ['id', 'title', 'time', 'price', 'nomenclature', 'equipment', 'rank', 'is_active']

    def create(self, validated_data):
        op_noms_data = validated_data.pop('op_noms')
        operation = Operation.objects.create(**validated_data)

        consumable_list = []
        for op_nom_data in op_noms_data:
            consumables_data = op_nom_data.pop('consumables')
            # op_nom = OperationNom.objects.create(operation=operation, **op_nom_data)
            #
            # for consumable_data in consumables_data:
            #     consumable_list.append(
            #         Consumable(operation_nom=op_nom, **consumable_data)
            #     )
        Consumable.objects.bulk_create(consumable_list)

        return operation

    def update(self, instance, validated_data):
        op_noms_data = validated_data.pop('op_noms')

        for key, value in validated_data.items():
            setattr(instance, key, value)
        instance.save()

        instance.op_noms.all().delete()

        consumable_list = []

        for op_nom_data in op_noms_data:
            consumables_data = op_nom_data.pop('consumables')
            # for consumable_data in consumables_data:
            #     consumable_list.append(Consumable(operation_nom=op_nom, **consumable_data))

        Consumable.objects.bulk_create(consumable_list)
        return instance


class ProductListSerializer(serializers.ModelSerializer):
    time = serializers.SerializerMethodField()

    class Meta:
        model = Nomenclature
        fields = ['id', 'vendor_code', 'title', 'cost_price', 'time']

    def get_time(self, obj):
        # Суммируем время всех связанных операций
        return sum(operation.time for operation in obj.operations.all())



