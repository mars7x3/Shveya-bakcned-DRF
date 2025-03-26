from rest_framework import serializers

from my_db.models import Order, ClientProfile, OrderProductAmount, OrderProduct, PartyDetail, Party, Nomenclature, Size, \
    Color, StaffProfile


class OrderClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClientProfile
        fields = ('id', 'name', 'surname', 'company_title', 'phone')


class OrderListSerializer(serializers.ModelSerializer):
    client = OrderClientSerializer()

    class Meta:
        model = Order
        fields = ['id', 'client', 'status', 'deadline', 'created_at']


class NomenclatureSerializer(serializers.ModelSerializer):
    class Meta:
        model = Nomenclature
        fields = ['id', 'title', 'vendor_code']


class ColorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Color
        fields = ['id', 'title', 'code']


class SizeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Size
        fields = ['id', 'title']


class GETOrderProductAmountSerializer(serializers.ModelSerializer):
    size = SizeSerializer()
    color = ColorSerializer()
    cut = serializers.SerializerMethodField()

    class Meta:
        model = OrderProductAmount
        fields = ['size', 'amount', 'done', 'color', 'cut']

    def get_cut(self, obj):
        order = obj.order_product.order
        nomenclature = obj.order_product.nomenclature

        return sum(
            detail.true_amount
            for party in order.parties.filter(nomenclature=nomenclature)
            for detail in party.details.filter(color=obj.color, size=obj.size)
        )


class GETOrderProductSerializer(serializers.ModelSerializer):
    amounts = GETOrderProductAmountSerializer(many=True)
    nomenclature = NomenclatureSerializer()
    time = serializers.SerializerMethodField()

    class Meta:
        model = OrderProduct
        fields = ['nomenclature', 'price', 'true_price', 'cost_price', 'true_cost_price', 'amounts']

    def get_time(self, obj):
        return sum(operation.time for operation in obj.nomenclature.operations.all())


class GETPartyDetailSerializer(serializers.ModelSerializer):
    size = SizeSerializer()
    color = ColorSerializer()

    class Meta:
        model = PartyDetail
        fields = ['size', 'plan_amount', 'true_amount', 'color']


class StaffSerializer(serializers.ModelSerializer):
    class Meta:
        model = StaffProfile
        fields = ['name', 'surname']


class GETPartySerializer(serializers.ModelSerializer):
    details = GETPartyDetailSerializer(many=True)
    staff = StaffSerializer()

    class Meta:
        model = Party
        fields = ['nomenclature', 'staff', 'number', 'status', 'created_at', 'details']


class OrderDetailSerializer(serializers.ModelSerializer):
    client = OrderClientSerializer()
    products = GETOrderProductSerializer(many=True)
    parties = GETPartySerializer(many=True)

    class Meta:
        model = Order
        fields = ['id', 'client', 'status', 'deadline', 'created_at', 'true_deadline', 'products', 'parties']


class OrderProductAmountSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderProductAmount
        fields = ['size', 'amount', 'color', 'done']


class OrderProductSerializer(serializers.ModelSerializer):
    amounts = OrderProductAmountSerializer(many=True)

    class Meta:
        model = OrderProduct
        fields = ['nomenclature', 'price', 'amounts', 'cost_price', 'true_price', 'price', 'cost_price',
                  'true_cost_price']


class OrderCRUDSerializer(serializers.ModelSerializer):
    client = serializers.PrimaryKeyRelatedField(queryset=ClientProfile.objects.all(), required=True)
    products = OrderProductSerializer(many=True)

    class Meta:
        model = Order
        fields = ['deadline', 'client', 'products', 'status']

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