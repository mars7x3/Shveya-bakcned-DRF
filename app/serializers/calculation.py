from rest_framework import serializers

from my_db.models import Rank, Nomenclature, Operation, CalOperation, CalConsumable, CalPrice, Calculation, \
    ClientProfile, Consumable, Color, Price, Equipment, CalCombination, Combination
from utils.get_or_none import serialize_instance


class OperationRankSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rank
        fields = ['id', 'title']


class EquipmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Equipment
        fields = ['id', 'title']


class OperationDetailSerializer(serializers.ModelSerializer):
    rank = OperationRankSerializer(read_only=True)
    equipment = EquipmentSerializer()

    class Meta:
        model = Operation
        fields = ['id', 'title', 'time', 'equipment', 'rank']


class ConsumableDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Nomenclature
        fields = ['id', 'title', 'vendor_code', 'unit', 'cost_price']


class CalOperationSerializer(serializers.ModelSerializer):
    rank_info = serializers.SerializerMethodField()

    def get_rank_info(self, obj):
        return serialize_instance(
            obj.rank,
            ["id", "title"]
        )

    class Meta:
        model = CalOperation
        fields = ['id', 'title', 'time', 'price', 'rank', 'equipment', 'rank_info']


class CalCombinationSerializer(serializers.ModelSerializer):
    operations = CalOperationSerializer(many=True, required=False)

    class Meta:
        model = CalCombination
        fields = ['id', 'title', 'operations', 'status']


class CalConsumableSerializer(serializers.ModelSerializer):
    class Meta:
        model = CalConsumable
        fields = ['id', 'nomenclature', 'title', 'consumption', 'unit', 'price']


class CalPriceSerializer(serializers.ModelSerializer):
    class Meta:
        model = CalPrice
        fields = ['id', 'title', 'price']


class CalClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClientProfile
        fields = ['id', 'name', 'surname', 'company_title', 'phone', 'address', 'image']


class CalculationSerializer(serializers.ModelSerializer):
    combinations = CalCombinationSerializer(many=True, required=False)
    cal_consumables = CalConsumableSerializer(many=True, required=False)
    cal_prices = CalPriceSerializer(many=True, required=False)
    client_info = serializers.SerializerMethodField()

    def get_client_info(self, obj):
        return serialize_instance(
            obj.client,
            ["id", "name", "surename", "company_title", "phone", "combinations"]
        )

    class Meta:
        model = Calculation
        fields = ['id', 'vendor_code', 'client', 'title', 'count', 'is_active', 'price', 'cost_price', 'nomenclature',
                  'created_at', 'combinations', 'cal_consumables', 'cal_prices', 'client_info']
        read_only_fields = ['created_at']

    def create(self, validated_data):
        combinations = validated_data.pop('combinations', [])
        consumables_data = validated_data.pop('cal_consumables', [])
        prices_data = validated_data.pop('cal_prices', [])

        calculation = Calculation.objects.create(**validated_data)

        create_data = []
        for data in combinations:
            c_operations_data = data.pop('operations')
            combination = CalCombination.objects.create(calculation=calculation, **data)
            for o in c_operations_data:
                create_data.append(
                    CalOperation(combination=combination, **o)
                )
        CalOperation.objects.bulk_create(create_data)

        CalConsumable.objects.bulk_create([
            CalConsumable(calculation=calculation, **consumable) for consumable in consumables_data
        ])
        CalPrice.objects.bulk_create([
            CalPrice(calculation=calculation, **price) for price in prices_data
        ])

        return calculation

    def update(self, instance, validated_data):
        combinations = validated_data.pop('combinations', [])
        consumables_data = validated_data.pop('cal_consumables', [])
        prices_data = validated_data.pop('cal_prices', [])

        instance.vendor_code = validated_data.get('vendor_code', instance.vendor_code)
        instance.client = validated_data.get('client', instance.client)
        instance.title = validated_data.get('title', instance.title)
        instance.is_active = validated_data.get('is_active', instance.is_active)
        instance.price = validated_data.get('price', instance.price)
        instance.cost_price = validated_data.get('cost_price', instance.cost_price)
        instance.count = validated_data.get('count', instance.count)

        instance.save()

        instance.combinations.all().delete()

        create_data = []
        for data in combinations:
            c_operations_data = data.pop('operations')
            combination = CalCombination.objects.create(calculation=instance, **data)
            for o in c_operations_data:
                create_data.append(
                    CalOperation(combination=combination, **o)
                )
        CalOperation.objects.bulk_create(create_data)

        CalConsumable.objects.filter(calculation=instance).delete()
        CalConsumable.objects.bulk_create([
            CalConsumable(calculation=instance, **consumable) for consumable in consumables_data
        ])

        CalPrice.objects.filter(calculation=instance).delete()
        CalPrice.objects.bulk_create([
            CalPrice(calculation=instance, **price) for price in prices_data
        ])

        return instance


class CalculationListSerializer(serializers.ModelSerializer):
    client = CalClientSerializer(read_only=True)

    class Meta:
        model = Calculation
        fields = ['id', 'vendor_code', 'title', 'created_at', 'client']
        read_only_fields = ['created_at']


class ClientProfileListSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClientProfile
        fields = ['id', 'name', 'surname', 'company_title']


class ConsumableTitleListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Nomenclature
        fields = ['id', 'title', 'vendor_code', 'color', 'coefficient']


class GPListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Nomenclature
        fields = ['id', 'vendor_code', 'title']


class RankSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rank
        fields = ['id', 'title', 'percent']


class ColorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Color
        fields = ['id', 'title', 'code']


class GETOperationInfoSerializer(serializers.ModelSerializer):
    rank = RankSerializer()

    class Meta:
        model = Operation
        fields = ['id', 'title', 'time', 'price', 'rank']


class GETCombinationInfoSerializer(serializers.ModelSerializer):
    operations = GETOperationInfoSerializer(many=True)

    class Meta:
        model = Combination
        fields = ['id', 'title', 'status', 'operations']


class GPInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Nomenclature
        fields = ['id', 'vendor_code', 'title', 'cost_price', 'unit']


class GETConsumableInfoSerializer(serializers.ModelSerializer):
    material_nomenclature = GPInfoSerializer()

    class Meta:
        model = Consumable
        fields = ['material_nomenclature', 'consumption']


class GETPriceInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Price
        fields = ['title', 'price']


class GETProductInfoSerializer(serializers.ModelSerializer):
    combinations = GETCombinationInfoSerializer(many=True)
    consumables = GETConsumableInfoSerializer(many=True)
    prices = GETPriceInfoSerializer(many=True)

    class Meta:
        model = Nomenclature
        fields = ['id', 'vendor_code','title', 'combinations', 'consumables', 'prices']

