from rest_framework import serializers

from my_db.enums import NomType
from my_db.models import Warehouse, StaffProfile, Nomenclature, NomCount, Quantity, QuantityNomenclature, \
    QuantityHistory, QuantityFile


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
        if staffs_data:
            warehouse.staffs.set(staffs_data)
        return warehouse


class MaterialSerializer(serializers.ModelSerializer):
    class Meta:
        model = Nomenclature
        fields = ['id', 'title', 'vendor_code', 'unit', 'cost_price', 'color', 'coefficient', 'status']

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep['amount'] = instance.filtered_count_amount
        return rep


class MaterialCRUDSerializer(serializers.ModelSerializer):
    class Meta:
        model = Nomenclature
        fields = ['id', 'vendor_code', 'is_active', 'title', 'unit', 'color', 'coefficient', 'status', 'cost_price']

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


class CreateMaterialsDetailSerializer(serializers.Serializer):
    color = serializers.IntegerField()
    cost_price = serializers.DecimalField(max_digits=12, decimal_places=3)
    coefficient = serializers.DecimalField(max_digits=10, decimal_places=1)


class CreateMaterialsSerializer(serializers.Serializer):
    title = serializers.CharField()
    unit = serializers.IntegerField()
    details = CreateMaterialsDetailSerializer(many=True)


class StockInputSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    amount = serializers.IntegerField()
    price = serializers.IntegerField(required=False)
    comment = serializers.CharField(required=False)


class StockOutputSerializer(serializers.Serializer):
    output_warehouse_id = serializers.IntegerField(required=False)
    products = StockInputSerializer(many=True)
    status = serializers.IntegerField(required=False)


class StockDefectiveSerializer(serializers.Serializer):
    products = StockInputSerializer(many=True)
    status = serializers.IntegerField()


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
        fields = ['id', 'title', 'color', 'vendor_code']


class OutputWarehouseMaterialsSerializer(serializers.ModelSerializer):
    nomenclature = OutputWarehouseNomSerializer()

    class Meta:
        model = QuantityNomenclature
        fields = ['nomenclature', 'amount']


class MovingSerializer(serializers.ModelSerializer):
    quantities = OutputWarehouseMaterialsSerializer(many=True)
    out_warehouse = OutputWarehouseSerializer()

    class Meta:
        model = Quantity
        fields = ['id', 'quantities', 'out_warehouse']


class MovingListSerializer(serializers.ModelSerializer):
    out_warehouse = OutputWarehouseSerializer()

    class Meta:
        model = Quantity
        fields = ['id', 'out_warehouse', 'created_at']


class MyMaterialsSerializer(serializers.ModelSerializer):

    class Meta:
        model = Nomenclature
        fields = ['id', 'title', 'vendor_code', 'unit', 'cost_price', 'is_active', 'color', 'coefficient', 'status']

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        if instance.filtered_counts:
            rep['amount'] = instance.filtered_counts[0].amount
        else:
            rep['amount'] = 0
        return rep


class WarehouseListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Warehouse
        fields = ['id', 'title', 'address']


class QuantitySerializer(serializers.ModelSerializer):
    in_warehouse = WarehouseListSerializer()
    out_warehouse = WarehouseListSerializer()

    class Meta:
        model = Quantity
        fields = ['id', 'in_warehouse', 'out_warehouse', 'order']


class QuantityHistoryListSerializer(serializers.ModelSerializer):
    quantity = QuantitySerializer()

    class Meta:
        model = QuantityHistory
        fields = ['id', 'staff_id', 'staff_name', 'staff_surname', 'status', 'created_at', 'quantity']


class NomenclatureSerializer(serializers.ModelSerializer):
    class Meta:
        model = Nomenclature
        fields = ['id', 'title', 'vendor_code', 'unit', 'color']


class QuantityNomenclatureSerializer(serializers.ModelSerializer):
    nomenclature = NomenclatureSerializer()

    class Meta:
        model = QuantityNomenclature
        fields = ['nomenclature', 'amount', 'price', 'comment']


class QuantityFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuantityFile
        fields = ['file']


class QuantityDetailSerializer(serializers.ModelSerializer):
    in_warehouse = WarehouseListSerializer()
    out_warehouse = WarehouseListSerializer()
    quantities = QuantityNomenclatureSerializer(many=True)
    files = QuantityFileSerializer(many=True)

    class Meta:
        model = Quantity
        fields = ['id', 'in_warehouse', 'out_warehouse', 'quantities', 'files', 'status', 'created_at', 'order']


class QuantityHistoryDetailSerializer(serializers.ModelSerializer):
    quantity = QuantityDetailSerializer()

    class Meta:
        model = QuantityHistory
        fields = ['id', 'staff_id', 'staff_name', 'staff_surname', 'status', 'created_at', 'quantity']
