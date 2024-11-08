from rest_framework import serializers

from my_db.enums import NomType
from my_db.models import Nomenclature, Pattern, Operation, Combination, Rank, Equipment, Consumable, Size, \
    OperationNom


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


class CombinationOperationsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Operation
        fields = ['id', 'title']


class CombinationSerializer(serializers.ModelSerializer):
    operations = CombinationOperationsSerializer(many=True)

    class Meta:
        model = Combination
        fields = '__all__'


class NomenclatureSerializer(serializers.ModelSerializer):
    class Meta:
        model = Nomenclature
        fields = ['id', 'title', 'unit']


class EquipmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Equipment
        fields = ['id', 'title']


class Rank2Serializer(serializers.ModelSerializer):
    class Meta:
        model = Rank
        fields = ['id', 'title']


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
    equipment = EquipmentSerializer()
    rank = Rank2Serializer()
    op_noms = OperationNomSerializer(many=True)

    class Meta:
        model = Operation
        fields = ['id', 'title', 'price', 'nomenclature', 'equipment', 'rank', 'is_active', 'op_noms']


class GPDetailSerializer(serializers.ModelSerializer):
    combinations = CombinationSerializer(read_only=True, many=True)
    operations = OperationSerializer(read_only=True, many=True)

    class Meta:
        model = Nomenclature
        fields = ['id', 'vendor_code', 'is_active', 'title', 'combinations', 'operations']


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


class CombinationCRUDSerializer(CombinationSerializer):
    operations = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Nomenclature.objects.all()
    )


class ConsumableCRUDSerializer(serializers.ModelSerializer):
    class Meta:
        model = Consumable
        fields = ['id', 'size', 'consumption', 'waste']
        extra_kwargs = {'id': {'read_only': True, 'required': False}}


class OperationNomCRUDSerializer(serializers.ModelSerializer):
    consumables = ConsumableCRUDSerializer(many=True)

    class Meta:
        model = OperationNom
        fields = ['id', 'nomenclature', 'consumables']
        extra_kwargs = {'id': {'read_only': True, 'required': False}}


class OperationCRUDSerializer(serializers.ModelSerializer):
    op_noms = OperationNomCRUDSerializer(many=True)

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