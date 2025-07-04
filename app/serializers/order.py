from django.db import transaction
from django.db.models import Sum
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from my_db.enums import CombinationStatus, OrderStatus, QuantityStatus
from my_db.models import Order, ClientProfile, OrderProductAmount, OrderProduct, PartyDetail, Party, Nomenclature, Size, \
    Color, StaffProfile, WorkDetail, Warehouse, Quantity, QuantityNomenclature, QuantityHistory, NomCount


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
    otk = serializers.SerializerMethodField()

    class Meta:
        model = OrderProductAmount
        fields = ['size', 'amount', 'done', 'color', 'cut', 'defect', 'otk']

    def get_cut(self, obj):
        order = obj.order_product.order
        nomenclature = obj.order_product.nomenclature

        return sum(
            detail.true_amount
            for party in order.parties.filter(nomenclature=nomenclature)
            for detail in party.details.filter(color=obj.color, size=obj.size)
        )

    def get_otk(self, obj):
        order = obj.order_product.order
        nomenclature = obj.order_product.nomenclature

        return (
                WorkDetail.objects.filter(
                    work__party__in=order.parties.filter(nomenclature=nomenclature),
                    work__color=obj.color,
                    work__size=obj.size,
                    combination__status=CombinationStatus.DONE
                ).aggregate(total=Sum('amount'))['total'] or 0
        )


class GETOrderProductSerializer(serializers.ModelSerializer):
    amounts = GETOrderProductAmountSerializer(many=True)
    nomenclature = NomenclatureSerializer()
    time = serializers.SerializerMethodField()

    class Meta:
        model = OrderProduct
        fields = ['nomenclature', 'price', 'true_price', 'cost_price', 'true_cost_price', 'amounts', 'time']

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


class WarehouseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Warehouse
        fields = ['id', 'title']


class OrderDetailSerializer(serializers.ModelSerializer):
    client = OrderClientSerializer()
    products = GETOrderProductSerializer(many=True)
    parties = GETPartySerializer(many=True)
    in_warehouse = WarehouseSerializer()
    out_warehouse = WarehouseSerializer()

    class Meta:
        model = Order
        fields = ['id', 'client', 'status', 'deadline', 'created_at', 'true_deadline', 'products', 'parties',
                  'in_warehouse', 'out_warehouse']


class OrderProductAmountSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderProductAmount
        fields = ['size', 'amount', 'color', 'done', 'defect']


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
        fields = ['deadline', 'client', 'products', 'status', 'in_warehouse', 'out_warehouse']

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
        if instance.status == OrderStatus.DONE:
            raise ValidationError("Вы не можете редактировать заказ, так как он уже готов.")

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

        if instance.status == OrderStatus.DONE and instance.warehouse:
            data = [
                {
                    "product_id": product.nomenclature.id,
                    "amount": sum(amount.done for amount in product.amounts.all()),
                    "price": product.true_price,
                }
                for product in instance.products.all()
            ]

            quantity = Quantity.objects.create(in_warehouse=instance.warehouse, status=QuantityStatus.ACTIVE)

            create_data = []
            for i in data:
                create_data.append(
                    QuantityNomenclature(
                        quantity=quantity,
                        nomenclature_id=i['product_id'],
                        amount=i['amount'],
                        price=i['price'],
                    )
                )
            QuantityNomenclature.objects.bulk_create(create_data)

            staff = self.context['request'].user.staff_profile
            QuantityHistory.objects.create(quantity=quantity, staff_id=staff.id, staff_name=staff.name,
                                           staff_surname=staff.surname, status=quantity.status)

            with transaction.atomic():
                nom_count_updates = []
                nomenclature_updates = []

                for item in data:
                    obj, created = NomCount.objects.get_or_create(
                        warehouse=quantity.in_warehouse,
                        nomenclature_id=item["product_id"]
                    )
                    if created:
                        obj.amount = item['amount']
                        obj.save()

                    else:
                        obj.amount += item["amount"]
                    nom_count_updates.append(obj)

                    nomenclature = Nomenclature.objects.get(id=item['product_id'])

                    total_amount_before = NomCount.objects.filter(nomenclature_id=item['product_id']).aggregate(
                        total_amount=Sum('amount')
                    )['total_amount'] or 0
                    if total_amount_before > 0:
                        total_amount_before -= item['amount']
                    total_cost_before = total_amount_before * nomenclature.cost_price

                    total_amount_after = obj.amount
                    total_cost_after = total_cost_before + (item['amount'] * item['price'])

                    nomenclature.cost_price = total_cost_after / total_amount_after
                    nomenclature_updates.append(nomenclature)

                NomCount.objects.bulk_update(nom_count_updates, ['amount'])
                Nomenclature.objects.bulk_update(nomenclature_updates, ['cost_price'])


        return instance