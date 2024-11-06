from rest_framework import serializers

from my_db.models import Rank, Size, SizeCategory


class RankSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rank
        fields = '__all__'


class SizeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Size
        fields = '__all__'


class SizeCategorySerializer(serializers.ModelSerializer):
    sizes = SizeSerializer(many=True, read_only=True)

    class Meta:
        model = SizeCategory
        fields = ['id', 'title', 'is_active', 'sizes']

