from django.db.models import IntegerField
from rest_framework import serializers

from my_db.enums import NomType
from my_db.models import Warehouse, StaffProfile, Nomenclature, NomCount, Quantity, QuantityNomenclature


class WarehouseStaffSerializer(serializers.ModelSerializer):
    class Meta:
        model = StaffProfile
        fields = ['id', 'name', 'surname']


class WarehouseSerializer(serializers.ModelSerializer):
    staffs = WarehouseStaffSerializer(many=True)

    class Meta:
        model = Warehouse
        fields = ['id', 'title', 'address', 'staffs']


class WarehouseCRUDSerializer(WarehouseSerializer):
    staffs = serializers.PrimaryKeyRelatedField(
        queryset=StaffProfile.objects.all(),
        required=False,
        many=True
    )

    def create(self, validated_data):
        staffs_data = validated_data.pop('staffs', [])
        warehouse = super().create(validated_data)
        if staffs_data:
            warehouse.staffs.set(staffs_data)
        return warehouse

    def update(self, instance, validated_data):
        staffs_data = validated_data.pop('staffs', [])
        warehouse = super().update(instance, validated_data)
        warehouse.staffs.all().delete()
        if staffs_data:
            warehouse.staffs.set(staffs_data)
        return warehouse


class MaterialSerializer(serializers.ModelSerializer):
    class Meta:
        model = Nomenclature
        fields = ['id', 'title', 'vendor_code', 'unit', 'cost_price']

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep['amount'] = instance.filtered_count_amount
        return rep


class MaterialCRUDSerializer(serializers.ModelSerializer):
    class Meta:
        model = Nomenclature
        fields = ['id', 'vendor_code', 'is_active', 'title', 'unit']

    def validate(self, attrs):
        attrs['type'] = NomType.MATERIAL
        return attrs

    def create(self, validated_data):
        obj = super().create(validated_data)
        create_data = []
        for w in Warehouse.objects.all():
            create_data.append(NomCount(warehouse=w, nomenclature=obj))

        NomCount.objects.bulk_create(create_data)
        return obj


class StockInputSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    amount = serializers.IntegerField()
    price = serializers.IntegerField(required=False)


class StockOutputSerializer(serializers.Serializer):
    output_warehouse_id = serializers.IntegerField()
    products = StockInputSerializer(many=True)


class StockDefectiveSerializer(serializers.Serializer):
    comment = serializers.CharField(required=False)
    products = StockInputSerializer(many=True)


class StockDefectiveFileSerializer(serializers.Serializer):
    quantity_id = serializers.IntegerField()
    files = serializers.ListField(
        child=serializers.FileField(allow_empty_file=False, required=False),
        required=False
    )


class StockOutputUpdateSerializer(serializers.Serializer):
    quantity_id = serializers.IntegerField()
    status = serializers.IntegerField()


class OutputWarehouseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Warehouse
        fields = ['id', 'title']


class OutputWarehouseNomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Nomenclature
        fields = ['id', 'title']


class OutputWarehouseMaterialsSerializer(serializers.ModelSerializer):
    nomenclature = OutputWarehouseNomSerializer()
    class Meta:
        model = QuantityNomenclature
        fields = ['nomenclature', 'amount']


class MovingSerializer(serializers.ModelSerializer):
    quantities = OutputWarehouseMaterialsSerializer(many=True)
    class Meta:
        model = Quantity
        fields = ['id', 'quantities']


class MovingListSerializer(serializers.ModelSerializer):
    out_warehouse = OutputWarehouseSerializer()
    class Meta:
        model = Quantity
        fields = ['id', 'out_warehouse', 'created_at']


class MyMaterialsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Nomenclature
        fields = ['id', 'title', 'vendor_code', 'unit', 'cost_price', 'is_active']

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep['amount'] = instance.filtered_counts[0].amount
        return rep

