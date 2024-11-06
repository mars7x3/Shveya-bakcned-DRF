from rest_framework import serializers

from my_db.models import Order, ClientProfile


class OrderClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClientProfile
        fields = ('name', 'surname', 'company_title')


class OrderSerializer(serializers.ModelSerializer):
    client = OrderClientSerializer(read_only=True)

    class Meta:
        model = Order
        fields = '__all__'