from rest_framework import serializers

from my_db.models import Order, ClientProfile, OrderProductAmount, OrderProduct


class OrderClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClientProfile
        fields = ('name', 'surname', 'company_title')


class OrderSerializer(serializers.ModelSerializer):
    client = OrderClientSerializer(read_only=True)
    completion_percentage = serializers.FloatField()
    total_cost = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        model = Order
        fields = [
            'id',
            'client',
            'status',
            'deadline',
            'created_at',
            'total_cost',
            'total_revenue',
            'completion_percentage'
        ]


class OrderProductAmountSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderProductAmount
        fields = ['size', 'amount', 'color']


class OrderProductSerializer(serializers.ModelSerializer):
    amounts = OrderProductAmountSerializer(many=True)

    class Meta:
        model = OrderProduct
        fields = ['nomenclature', 'price', 'amounts', 'cost_price']


class OrderCRUDSerializer(serializers.ModelSerializer):
    client = serializers.PrimaryKeyRelatedField(queryset=ClientProfile.objects.all(), required=True)
    products = OrderProductSerializer(many=True)

    class Meta:
        model = Order
        fields = ['deadline', 'client', 'products', 'status']
        extra_kwargs = {'status': {'read_only': True, 'required': False}}

    def create(self, validated_data):
        products_data = validated_data.pop('products')
        order = Order.objects.create(**validated_data)

        order_products_list = []
        for product_data in products_data:
            amounts_data = product_data.pop('amounts')
            order_product = OrderProduct.objects.create(order=order, **product_data)

            for amount_data in amounts_data:
                order_products_list.append(
                    OrderProductAmount(order_product=order_product, **amount_data)
                )
        OrderProductAmount.objects.bulk_create(order_products_list)

        return order

    def update(self, instance, validated_data):
        products_data = validated_data.pop('products')

        for key, value in validated_data.items():
            setattr(instance, key, value)
        instance.save()

        instance.products.all().delete()
        order_products_list = []
        for product_data in products_data:
            amounts_data = product_data.pop('amounts')
            order_product = OrderProduct.objects.create(order=instance, **product_data)

            for amount_data in amounts_data:
                order_products_list.append(
                    OrderProductAmount(order_product=order_product, **amount_data)
                )

        OrderProductAmount.objects.bulk_create(order_products_list)

        return instance