from django.db.models import Sum, F, DecimalField, ExpressionWrapper
from rest_framework import serializers

from my_db.models import PaymentFile, Payment, WorkDetail, Operation, StaffProfile


class WorkPaymentFileCRUDSerializer(serializers.Serializer):
    payment_id = serializers.IntegerField(help_text="ID payment, к которому добавляются файлы.")
    files = serializers.ListField(
        child=serializers.FileField(),
    )


class WorkPaymentFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentFile
        fields = ['file']


class WorkPaymentSerializer(serializers.ModelSerializer):
    files = WorkPaymentFileSerializer(many=True, read_only=True)

    class Meta:
        model = Payment
        fields = '__all__'


class WorkOperationSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField()
    price = serializers.IntegerField()


class GroupedWorkDetailSerializer(serializers.Serializer):
    operation = WorkOperationSerializer()
    total_amount = serializers.IntegerField()
    party_number = serializers.CharField()
    order_id = serializers.IntegerField()



class WorkDetailPaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ['id', 'amount', 'status', 'created_at']


class SalaryInfoSerializer(serializers.Serializer):
    works = GroupedWorkDetailSerializer(many=True)
    payments = WorkDetailPaymentSerializer(many=True)


class SalaryCreateSerializer(serializers.Serializer):
    staff_id = serializers.PrimaryKeyRelatedField(queryset=StaffProfile.objects.all())
    amount = serializers.IntegerField()


class AggregatedOperationSerializer(serializers.Serializer):
    operation_title = serializers.CharField()
    total_amount = serializers.IntegerField()
    operation_price = serializers.DecimalField(max_digits=12, decimal_places=3)
    total_price = serializers.DecimalField(max_digits=12, decimal_places=3)


class StaffProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = StaffProfile
        fields = ['id', 'name', 'surname', 'number', 'role']


class WorkPaymentDetailSerializer(serializers.ModelSerializer):
    files = WorkPaymentFileSerializer(many=True, read_only=True)
    operations = serializers.SerializerMethodField()
    staff = StaffProfileSerializer()

    class Meta:
        model = Payment
        fields = ['id', 'status', 'comment', 'created_at', 'amount', 'operations', 'files', 'staff']

    def get_operations(self, obj):
        operations = (
            WorkDetail.objects.filter(payment=obj)
            .annotate(
                operation_title=F('combination__title'),
                operation_price=F('combination__operations__price'),
                total_amount=Sum('amount'),
            )
            .annotate(
                total_price=ExpressionWrapper(
                    F('operation_price') * F('total_amount'),
                    output_field=DecimalField(max_digits=10, decimal_places=2)
                )
            )
            .values('operation_title', 'operation_price', 'total_amount', 'total_price')
        )
        return AggregatedOperationSerializer(operations, many=True).data
