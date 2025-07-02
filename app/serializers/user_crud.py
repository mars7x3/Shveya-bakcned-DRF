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
        fields = ['username', 'password', 'is_active']


class MyUserUpdateSerializer(serializers.ModelSerializer):
    username = serializers.CharField(required=False)
    password = serializers.CharField(required=False)
    is_active = serializers.BooleanField(required=False)

    class Meta:
        model = MyUser
        fields = ['username', 'password', 'is_active']


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
        warehouse = instance.warehouses.first()
        if warehouse:
            rep['warehouse'] = StaffWarehouseSerializer(warehouse, context=self.context).data
        else:
            rep['warehouse'] = 'Не привязан склад к сотруднику.'
        return rep


class StaffCreateSerializer(StaffSerializer):
    rank = serializers.PrimaryKeyRelatedField(queryset=Rank.objects.all(), required=False)
    username = serializers.CharField(write_only=True, required=True)
    password = serializers.CharField(write_only=True, required=True)
    image = serializers.ImageField(required=False, allow_null=True)
    is_active = serializers.BooleanField()


class StaffUpdateSerializer(StaffCreateSerializer):
    image_delete = serializers.BooleanField(default=False)

    def validate(self, attrs):
        image_delete = attrs.get('image_delete', None)

        if image_delete:
            staff_profile = self.instance
            if staff_profile and staff_profile.image:
                staff_profile.image.delete(save=False)
                staff_profile.image = None
        return attrs


class ClientFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClientFile
        fields = ['id', 'file']


class ClientSerializer(serializers.ModelSerializer):
    user = MyUserSerializer(read_only=True)
    files = ClientFileSerializer(read_only=True, many=True)

    class Meta:
        model = ClientProfile
        fields = '__all__'


class ClientCreateSerializer(ClientSerializer):
    username = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True)
    image = serializers.ImageField(required=False, allow_null=True)


class ClientUpdateSerializer(ClientCreateSerializer):
    username = serializers.CharField(write_only=True, required=False)
    password = serializers.CharField(write_only=True, required=False)
    image_delete = serializers.BooleanField(default=False)

    def validate(self, attrs):
        image_delete = attrs.get('image_delete', None)

        if image_delete:
            client_profile = self.instance
            if client_profile and client_profile.image:
                client_profile.image.delete(save=False)
                client_profile.image = None
        return attrs


class ClientListSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClientProfile
        fields = ['id', 'name', 'surname', 'phone', 'address']


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


class StaffListSerializer(serializers.ModelSerializer):
    class Meta:
        model = StaffProfile
        fields = ['id', 'name', 'surname', 'number']
