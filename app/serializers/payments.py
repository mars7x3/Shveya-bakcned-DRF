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
    payments = WorkPaymentFileSerializer(many=True, read_only=True)

    class Meta:
        model = Payment
        fields = '__all__'


class WorkOperationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Operation
        fields = ['id', 'title']


class GroupedWorkDetailSerializer(serializers.Serializer):
    operation = WorkOperationSerializer()
    total_amount = serializers.IntegerField()
    price = serializers.IntegerField()



class SalaryInfoSerializer(serializers.Serializer):
    works = GroupedWorkDetailSerializer(many=True)
    payments = WorkPaymentSerializer(many=True)

    def to_representation(self, instance):
        return {
            "works": GroupedWorkDetailSerializer(instance['works'], many=True).data,
            "payments": WorkPaymentSerializer(instance['payments'], many=True).data,
        }


class SalaryCreateSerializer(serializers.Serializer):
    staff_id = serializers.PrimaryKeyRelatedField(queryset=StaffProfile.objects.all())
    amount = serializers.IntegerField()
