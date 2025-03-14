from collections import defaultdict

from rest_framework import serializers, status
from rest_framework.exceptions import ValidationError

from my_db.models import StaffProfile, Combination, Operation, Payment, PaymentFile, Nomenclature, Work, WorkDetail, \
    PartyConsumable, PartyDetail, Party, Order, OrderProduct, OrderProductAmount, Size, Color, ClientProfile, \
    Consumable


class OperationOutAndInSerializer(serializers.Serializer):
    operation_id = serializers.IntegerField()
    amount = serializers.IntegerField()


class WorkOutputSerializer(serializers.Serializer):
    order_id = serializers.IntegerField()
    staff_ids = serializers.ListSerializer(child=serializers.IntegerField())
    operations = OperationOutAndInSerializer(many=True)


class WorkInputSerializer(serializers.Serializer):
    order_id = serializers.IntegerField()
    staff_id = serializers.IntegerField()
    operations = OperationOutAndInSerializer(many=True)


class MyWorkInputSerializer(serializers.Serializer):
    order_id = serializers.IntegerField()
    operations = OperationOutAndInSerializer(many=True)


class WorkStaffListSerializer(serializers.ModelSerializer):
    class Meta:
        model = StaffProfile
        fields = ['id', 'name', 'surname', 'role']


class WorkOperationSerializer(serializers.ModelSerializer):
    required = serializers.IntegerField()
    assigned = serializers.IntegerField()
    completed = serializers.IntegerField()

    class Meta:
        model = Operation
        fields = ['id', 'title', 'required', 'assigned', 'completed']


class WorkCombinationSerializer(serializers.ModelSerializer):
    operations = WorkOperationSerializer(many=True)

    class Meta:
        model = Combination
        fields = ['id', 'title', 'operations']


class WorkNomenclatureSerializer(serializers.ModelSerializer):
    combinations = WorkCombinationSerializer(many=True)

    class Meta:
        model = Nomenclature
        fields = ['id', 'title', 'combinations']


class OperationSummarySerializer(serializers.Serializer):
    order_id = serializers.IntegerField()
    order_client = serializers.CharField()
    operation_id = serializers.IntegerField()
    operation_title = serializers.CharField()
    need_amount = serializers.IntegerField()
    done_amount = serializers.IntegerField()
    moderation_amount = serializers.IntegerField()


class WorkStaffSerializer(serializers.ModelSerializer):
    class Meta:
        model = StaffProfile
        fields = ['id', 'name', 'surname']


class OperationDetailSerializer(serializers.ModelSerializer):
    operation_title = serializers.CharField(source='operation.title')
    operation_id = serializers.IntegerField(source='operation.id')

    class Meta:
        model = WorkDetail
        fields = ['operation_id', 'operation_title', 'amount']


class WorkModerationListSerializer(serializers.ModelSerializer):
    staff = WorkStaffSerializer()
    details = OperationDetailSerializer(many=True)

    class Meta:
        model = Work
        fields = ['id', 'staff', 'details']


class WorkModerationSerializer(serializers.Serializer):
    work_id = serializers.IntegerField()


class PartyConsumableSerializer(serializers.ModelSerializer):
    class Meta:
        model = PartyConsumable
        fields = ['nomenclature', 'consumption', 'defect', 'left']


class PartyDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = PartyDetail
        fields = ['color', 'size', 'plan_amount', 'true_amount']


class PartyCreateUpdateSerializer(serializers.ModelSerializer):
    details = PartyDetailSerializer(many=True)
    consumptions = PartyConsumableSerializer(many=True)

    class Meta:
        model = Party
        fields = ['order', 'nomenclature', 'number', 'details', 'consumptions']

    def create(self, validated_data):
        details = validated_data.pop('details', [])
        consumptions = validated_data.pop('consumptions', [])

        party = Party.objects.create(**validated_data)

        PartyDetail.objects.bulk_create([
            PartyDetail(party=party, **data) for data in details
        ])
        PartyConsumable.objects.bulk_create([
            PartyConsumable(party=party, **consumable) for consumable in consumptions
        ])

        return party

    def update(self, instance, validated_data):
        details = validated_data.pop('details', [])
        consumptions = validated_data.pop('consumptions', [])

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        instance.details.all().delete()
        instance.consumptions.all().delete()

        PartyDetail.objects.bulk_create([
            PartyDetail(party=instance, **data) for data in details
        ])
        PartyConsumable.objects.bulk_create([
            PartyConsumable(party=instance, **consumable) for consumable in consumptions
        ])

        return instance



class NomenclatureSerializer(serializers.ModelSerializer):
    class Meta:
        model = Nomenclature
        fields = ['id', 'title', 'vendor_code', 'unit']


class PartyListSerializer(serializers.ModelSerializer):
    nomenclature = NomenclatureSerializer()

    class Meta:
        model = Party
        fields = ['id', 'order', 'nomenclature', 'number', 'status', 'created_at']


class SizeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Size
        fields = ['id', 'title']


class ColorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Color
        fields = ['id', 'title', 'code']


class PartyConsumableInfoSerializer(serializers.ModelSerializer):
    nomenclature = NomenclatureSerializer()

    class Meta:
        model = PartyConsumable
        fields = ['nomenclature', 'consumption', 'defect', 'left']


class PartyDetailInfoSerializer(serializers.ModelSerializer):
    color = ColorSerializer()
    size = SizeSerializer()

    class Meta:
        model = PartyDetail
        fields = ['color', 'size', 'plan_amount', 'true_amount']


class PartyGETInfoSerializer(serializers.ModelSerializer):
    nomenclature = NomenclatureSerializer()
    details = PartyDetailInfoSerializer(many=True)
    consumptions = PartyConsumableInfoSerializer(many=True)

    class Meta:
        model = Party
        fields = ['id', 'order', 'nomenclature', 'number', 'status', 'created_at', 'details', 'consumptions']


class OrderProductAmountSerializer(serializers.ModelSerializer):
    color = ColorSerializer()
    size = SizeSerializer()

    class Meta:
        model = OrderProductAmount
        fields = ['size', 'amount', 'color']


class OrderProductSerializer(serializers.ModelSerializer):
    nomenclature = NomenclatureSerializer(read_only=True)

    class Meta:
        model = OrderProduct
        fields = ['nomenclature']


class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClientProfile
        fields = ['name', 'surname', 'company_title']


class OrderSerializer(serializers.ModelSerializer):
    products = OrderProductSerializer(many=True)
    client = ClientSerializer()

    class Meta:
        model = Order
        fields = ['id', 'created_at', 'products', 'client']


class WorkDetailSerializer(serializers.Serializer):
    operation = serializers.IntegerField()
    color = serializers.IntegerField()
    size = serializers.IntegerField()
    amount = serializers.IntegerField()


class WorkSerializer(serializers.Serializer):
    party = serializers.IntegerField()
    nomenclature = serializers.IntegerField()
    details = WorkDetailSerializer(many=True)


class NomenclatureInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Nomenclature
        fields = ['id', 'title', 'vendor_code', 'image']


class ProductInfoSerializer(serializers.ModelSerializer):
    amounts = OrderProductAmountSerializer(many=True)
    nomenclature = NomenclatureInfoSerializer()

    class Meta:
        model = OrderProduct
        fields = ['nomenclature', 'amounts']


class InfoPartyDetailSerializer(serializers.ModelSerializer):
    color = ColorSerializer()
    size = SizeSerializer()

    class Meta:
        model = PartyDetail
        fields = ['color', 'size', 'true_amount']


class PartyInfoSerializer(serializers.ModelSerializer):
    details = InfoPartyDetailSerializer(many=True)

    class Meta:
        model = Party
        fields = ['id', 'number', 'details']


class RequestSerializer(serializers.Serializer):
    product = serializers.IntegerField()
    order = serializers.IntegerField()


class WorkCreateDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkDetail
        fields = ['staff', 'operation', 'amount']


class WorkCRUDSerializer(serializers.ModelSerializer):
    details = WorkCreateDetailSerializer(many=True)

    class Meta:
        model = Work
        fields = ['id', 'party', 'color', 'size', 'details']

    def validate(self, attrs):
        party = attrs.get('party')
        color = attrs.get('color')
        size = attrs.get('size')

        if Work.objects.filter(party=party, color=color, size=size).exists():
            raise ValidationError({'detail': 'Объект с такими party, color и size уже существует.'},
                                  code=status.HTTP_205_RESET_CONTENT)

        return attrs

    def create(self, validated_data):
        details = validated_data.pop('details')

        work = Work.objects.create(**validated_data)
        WorkDetail.objects.bulk_create([
            WorkDetail(work=work, **data) for data in details
        ])


        return work

    def update(self, instance, validated_data):
        details = validated_data.pop('details')
        instance.details.all().delete()

        WorkDetail.objects.bulk_create([
            WorkDetail(work=instance, **data) for data in details
        ])

        return instance


class OperationReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Operation
        fields = ['id', 'title']


class WorkDetailReadSerializer(serializers.ModelSerializer):
    staff = WorkStaffSerializer()
    operation = OperationReadSerializer()

    class Meta:
        model = WorkDetail
        fields = ['staff', 'operation', 'amount']


class GETWorkDetailSerializer(serializers.ModelSerializer):
    staff = WorkStaffSerializer()
    size = SizeSerializer()
    color = ColorSerializer()
    details = WorkDetailReadSerializer(many=True)
    party_amount = serializers.SerializerMethodField()

    class Meta:
        model = Work
        fields = ['id', 'created_at', 'updated_at', 'staff', 'size', 'color', 'party', 'details', 'party_amount']

    def get_party_amount(self, obj):
        if not obj.party:
            return None
        return (
            obj.party.details
            .filter(color=obj.color, size=obj.size)
            .first()
            .true_amount
            if obj.party.details.filter(color=obj.color, size=obj.size).exists()
            else 0
        )


class PartySerializer(serializers.ModelSerializer):
    class Meta:
        model = Party
        fields = ['id', 'number']


class GETWorkListSerializer(serializers.ModelSerializer):
    staff = WorkStaffSerializer()
    size = SizeSerializer()
    color = ColorSerializer()
    party = PartySerializer()

    class Meta:
        model = Work
        fields = ['id', 'created_at', 'updated_at', 'staff', 'size', 'color', 'party']


