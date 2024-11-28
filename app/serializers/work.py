from rest_framework import serializers

from my_db.models import StaffProfile, Combination, Operation


class OperationOutputSerializer(serializers.Serializer):
    operation_id = serializers.IntegerField()
    amount = serializers.IntegerField()


class WorkOutputSerializer(serializers.Serializer):
    order_id = serializers.IntegerField()
    staff_ids = serializers.ListSerializer(child=serializers.IntegerField())
    operations = OperationOutputSerializer(many=True)


class WorkStaffListSerializer(serializers.ModelSerializer):
    class Meta:
        model = StaffProfile
        fields = ['id', 'name', 'surname', 'role']


class WorkOperationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Operation
        fields = ['id', 'title']

class WorkCombinationSerializer(serializers.ModelSerializer):
    operations = WorkOperationSerializer(many=True)

    class Meta:
        model = Combination
        fields = ['id', 'title', 'operations']
