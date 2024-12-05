from rest_framework import serializers

from my_db.models import StaffProfile, Combination, Operation, Payment, PaymentFile, Nomenclature, Work


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


class WorkModerationListSerializer(serializers.ModelSerializer):
    staff = WorkStaffSerializer()

    class Meta:
        model = Work
        fields = ['id', 'staff', 'order', 'status', 'created_at']


class WorkModerationSerializer(serializers.Serializer):
    work_id = serializers.IntegerField()