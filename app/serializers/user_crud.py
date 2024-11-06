from rest_framework import serializers

from my_db.models import MyUser, StaffProfile, Rank, ClientProfile
from serializers.general import RankSerializer


class MyUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = MyUser
        fields = ['id', 'username', 'is_active']


class MyUserCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = MyUser
        fields = ['username', 'password']


class MyUserUpdateSerializer(serializers.ModelSerializer):
    username = serializers.CharField(required=False)
    password = serializers.CharField(required=False)

    class Meta:
        model = MyUser
        fields = ['username', 'password']


class StaffSerializer(serializers.ModelSerializer):
    user = MyUserSerializer(read_only=True)
    rank = RankSerializer(read_only=True)

    class Meta:
        model = StaffProfile
        fields = '__all__'


class StaffCreateUpdateSerializer(StaffSerializer):
    rank = serializers.PrimaryKeyRelatedField(queryset=Rank.objects.all())
    username = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True)
    image = serializers.ImageField(required=False, allow_null=True)

    def validate(self, attrs):
        image = attrs.get('image', None)

        if image is None:
            staff_profile = self.instance
            if staff_profile and staff_profile.image:
                staff_profile.image.delete(save=False)
                staff_profile.image = None
        return attrs



class ClientSerializer(serializers.ModelSerializer):
    user = MyUserSerializer(read_only=True)

    class Meta:
        model = ClientProfile
        fields = '__all__'


class ClientCreateUpdateSerializer(ClientSerializer):
    username = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True)
    image = serializers.ImageField(required=False, allow_null=True)





