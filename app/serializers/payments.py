from django.db.models import Sum, F
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


class WorkPaymentDetailSerializer(serializers.ModelSerializer):
    files = WorkPaymentFileSerializer(many=True, read_only=True)
    operations = serializers.SerializerMethodField()

    class Meta:
        model = Payment
        fields = ['id', 'status', 'comment', 'created_at', 'amount', 'operations', 'files']

    def get_operations(self, obj):
        operations = (
            WorkDetail.objects.filter(payment=obj)
            .annotate(
                operation_title=F('operation__title'),
                operation_price=F('operation__price'),
                total_amount=Sum('amount')
            )
            .values('operation_title', 'operation_price', 'total_amount')
        )
        return AggregatedOperationSerializer(operations, many=True).data