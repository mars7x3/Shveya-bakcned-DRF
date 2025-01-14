from rest_framework import serializers

from my_db.models import Rank, Size


class RankSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rank
        fields = '__all__'


class SizeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Size
        fields = '__all__'


class SizeCreateSerializer(serializers.Serializer):
    title = serializers.CharField()

