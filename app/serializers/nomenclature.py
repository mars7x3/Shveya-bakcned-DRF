from rest_framework import serializers

from my_db.enums import NomType
from my_db.models import Nomenclature, Pattern, Operation, Combination, Rank, Equipment, Consumable, Size, \
    OperationNom, SizeCategory


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


class EquipmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Equipment
        fields = ['id', 'title']


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
        operations_data = validated_data.pop('operations', [])
        combination = super().update(instance, validated_data)
        combination.operations.all().delete()
        if operations_data:
            combination.operations.set(operations_data)
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
        fields = ['id', 'size', 'consumption', 'waste']


class OperationNomSerializer(serializers.ModelSerializer):
    nomenclature = NomenclatureSerializer()
    consumables = ConsumableSerializer(many=True)

    class Meta:
        model = OperationNom
        fields = ['id', 'nomenclature', 'consumables']


class OperationSerializer(serializers.ModelSerializer):
    op_noms = OperationNomSerializer(many=True)

    class Meta:
        model = Operation
        fields = ['id', 'title', 'price', 'time', 'nomenclature', 'equipment', 'rank', 'is_active', 'op_noms']


class GPDetailSerializer(serializers.ModelSerializer):
    combinations = CombinationSerializer(read_only=True, many=True)
    operations = OperationSerializer(read_only=True, many=True)

    class Meta:
        model = Nomenclature
        fields = ['id', 'vendor_code', 'is_active', 'title', 'combinations', 'operations', 'category']


class GPCRUDSerializer(serializers.ModelSerializer):
    class Meta:
        model = Nomenclature
        fields = ['id', 'vendor_code', 'is_active', 'title', 'category']

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
        fields = ['size', 'consumption', 'waste']


class OperationNomCRUDSerializer(serializers.ModelSerializer):
    consumables = ConsumableCRUDSerializer(many=True)

    class Meta:
        model = OperationNom
        fields = ['nomenclature', 'consumables']


class OperationCRUDSerializer(serializers.ModelSerializer):
    op_noms = OperationNomCRUDSerializer(many=True, )

    class Meta:
        model = Operation
        fields = ['id', 'title', 'time', 'price', 'nomenclature', 'equipment', 'rank', 'is_active', 'op_noms']

    def create(self, validated_data):
        op_noms_data = validated_data.pop('op_noms')
        operation = Operation.objects.create(**validated_data)

        consumable_list = []
        for op_nom_data in op_noms_data:
            consumables_data = op_nom_data.pop('consumables')
            op_nom = OperationNom.objects.create(operation=operation, **op_nom_data)

            for consumable_data in consumables_data:
                consumable_list.append(
                    Consumable(operation_nom=op_nom, **consumable_data)
                )
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
            op_nom = OperationNom.objects.create(operation=instance, **op_nom_data)

            op_nom.consumables.all().delete()

            for consumable_data in consumables_data:
                consumable_list.append(Consumable(operation_nom=op_nom, **consumable_data))

        Consumable.objects.bulk_create(consumable_list)
        return instance


class SizeCategory2Serializer(serializers.ModelSerializer):
    class Meta:
        model = SizeCategory
        fields = ['id', 'title']


class ProductListSerializer(serializers.ModelSerializer):
    category = SizeCategory2Serializer()

    class Meta:
        model = Nomenclature
        fields = ['id', 'vendor_code', 'title', 'cost_price', 'category']

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        if instance.category:
            rep['sizes'] = Size2Serializer(instance.category.sizes.all(), many=True).data

        return rep
