from rest_framework import serializers

from my_db.enums import StaffRole
from my_db.models import MyUser, StaffProfile, Rank, ClientProfile, Warehouse, ClientFile
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


class StaffWarehouseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Warehouse
        fields = ['id', 'title', 'address']


class StaffRankSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rank
        fields = ['id', 'title']


class StaffSerializer(serializers.ModelSerializer):
    rank = StaffRankSerializer()
    user = MyUserSerializer(read_only=True)

    class Meta:
        model = StaffProfile
        fields = '__all__'
        extra_kwargs = {'user': {'read_only': True, 'required': False}}


    def to_representation(self, instance):
        rep = super().to_representation(instance)
        if instance.role == StaffRole.WAREHOUSE:
            rep['warehouse'] = StaffWarehouseSerializer(instance.warehouses.first(), context=self.context).data
        return rep


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


class ClientFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClientFile
        fields = ['file']


class ClientSerializer(serializers.ModelSerializer):
    user = MyUserSerializer(read_only=True)
    files = ClientFileSerializer(read_only=True, many=True)

    class Meta:
        model = ClientProfile
        fields = '__all__'


class ClientCreateUpdateSerializer(ClientSerializer):
    username = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True)
    image = serializers.ImageField(required=False, allow_null=True)



class ClientListSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClientProfile
        fields = ['id', 'name', 'surname', 'email', 'phone', 'address']


class ClientFileCRUDSerializer(serializers.Serializer):
    client_id = serializers.IntegerField(help_text="ID клиента, к которому добавляются изображения.")
    files = serializers.ListField(
        child=serializers.FileField(),
        required=False,
        help_text="Список файлов для добавления к клиенту."
    )
    delete_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        help_text="Список ID файлов для удаления. PS: в свагере не работает это место, "
                  "но если отправишь [1, 2], то сработает"
    )
