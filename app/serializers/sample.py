from rest_framework import serializers

from my_db.models import CombinationFile, Operation, Combination, Equipment, Rank


class FileCombinationListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Combination
        fields = ['id', 'title']


class CombinationFileDetailSerializer(serializers.ModelSerializer):
    combinations = FileCombinationListSerializer(many=True, read_only=True)

    class Meta:
        model = CombinationFile
        fields = ['id', 'title', 'combinations']


class CombinationFileCRUDSerializer(serializers.ModelSerializer):
    class Meta:
        model = CombinationFile
        fields = ['id', 'title']


class EquipmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Equipment
        fields = ['id', 'title']


class RankSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rank
        fields = ['id', 'title']


class OperationDetailSerializer(serializers.ModelSerializer):
    rank = RankSerializer()
    equipment = EquipmentSerializer()

    class Meta:
        model = Operation
        fields = ['id', 'title', 'time', 'price', 'equipment', 'rank', 'is_sample', 'is_active']


class OperationListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Operation
        fields = ['id', 'title']


class CombinationDetailSerializer(serializers.ModelSerializer):
    operations = OperationDetailSerializer(many=True)
    file = CombinationFileCRUDSerializer()

    class Meta:
        model = Combination
        fields = ['id', 'title', 'file', 'is_sample', 'operations', 'status']


class CombinationListSerializer(serializers.ModelSerializer):
    file = CombinationFileCRUDSerializer()

    class Meta:
        model = Combination
        fields = ['id', 'title', 'file']






