from rest_framework import serializers

from my_db.models import Rank, Nomenclature, Operation, CalOperation, CalConsumable, CalPrice, Calculation, \
    ClientProfile


class OperationRankSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rank
        fields = ['id', 'title']


class OperationNomenclatureSerializer(serializers.ModelSerializer):
    class Meta:
        model = Nomenclature
        fields = ['id', 'vendor_code', 'title']


class OperationDetailSerializer(serializers.ModelSerializer):
    nomenclature = OperationNomenclatureSerializer()
    rank = OperationRankSerializer()

    class Meta:
        model = Operation
        fields = ['id', 'title', 'time', 'nomenclature', 'rank']


class ConsumableDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Nomenclature
        fields = ['id', 'title', 'vendor_code', 'unit', 'cost_price']


class CalOperationSerializer(serializers.ModelSerializer):
    rank = OperationRankSerializer(required=False)

    class Meta:
        model = CalOperation
        fields = ['id', 'operation', 'title', 'time', 'price', 'rank']


class CalConsumableSerializer(serializers.ModelSerializer):
    class Meta:
        model = CalConsumable
        fields = ['id', 'nomenclature', 'title', 'consumption', 'unit']


class CalPriceSerializer(serializers.ModelSerializer):
    class Meta:
        model = CalPrice
        fields = ['id', 'title', 'price']


class CalClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClientProfile
        fields = ['name', 'surname', 'company_title', 'phone', 'address', 'image']


class CalculationSerializer(serializers.ModelSerializer):
    cal_operations = CalOperationSerializer(many=True, required=False)
    cal_consumables = CalConsumableSerializer(many=True, required=False)
    cal_prices = CalPriceSerializer(many=True, required=False)
    client = CalClientSerializer(read_only=True)

    class Meta:
        model = Calculation
        fields = ['id', 'vendor_code', 'client', 'title', 'count', 'is_active', 'price', 'cost_price', 'created_at',
                  'cal_operations', 'cal_consumables', 'cal_prices']
        read_only_fields = ['created_at']

    def create(self, validated_data):
        operations_data = validated_data.pop('cal_operations', [])
        consumables_data = validated_data.pop('cal_consumables', [])
        prices_data = validated_data.pop('cal_prices', [])

        calculation = Calculation.objects.create(**validated_data)

        CalOperation.objects.bulk_create([
            CalOperation(calculation=calculation, **operation) for operation in operations_data
        ])
        CalConsumable.objects.bulk_create([
            CalConsumable(calculation=calculation, **consumable) for consumable in consumables_data
        ])
        CalPrice.objects.bulk_create([
            CalPrice(calculation=calculation, **price) for price in prices_data
        ])

        return calculation

    def update(self, instance, validated_data):
        operations_data = validated_data.pop('cal_operations', [])
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

        CalOperation.objects.filter(calculation=instance).delete()
        CalOperation.objects.bulk_create([
            CalOperation(calculation=instance, **operation) for operation in operations_data
        ])

        CalConsumable.objects.filter(calculation=instance).delete()
        CalConsumable.objects.bulk_create([
            CalConsumable(calculation=instance, **consumable) for consumable in consumables_data
        ])

        CalPrice.objects.filter(calculation=instance).delete()
        CalPrice.objects.bulk_create([
            CalPrice(calculation=instance, **price) for price in prices_data
        ])

        return instance