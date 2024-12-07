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


class SizeCreateSerializer(serializers.Serializer):
    title = serializers.CharField()


class SizeCategorySerializer(serializers.ModelSerializer):
    sizes = SizeSerializer(many=True, read_only=True)
    sizes_add = serializers.ListField(
        child=SizeCreateSerializer(), required=False, write_only=True
    )
    sizes_delete = serializers.ListField(
        child=serializers.IntegerField(), required=False, write_only=True
    )

    class Meta:
        model = SizeCategory
        fields = ['id', 'title', 'is_active', 'sizes', 'sizes_add', 'sizes_delete']


