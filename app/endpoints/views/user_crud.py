from django.db.models import Q
from drf_spectacular.utils import extend_schema
from rest_framework import status, viewsets
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters import rest_framework as filters

from endpoints.permissions import IsDirectorAndTechnologist
from my_db.enums import UserStatus
from my_db.models import MyUser, StaffProfile, ClientProfile, ClientFile

from serializers.user_crud import StaffSerializer, StaffCreateUpdateSerializer, MyUserCreateSerializer, \
    MyUserUpdateSerializer, ClientSerializer, ClientCreateUpdateSerializer, MyUserSerializer, ClientListSerializer, \
    ClientFileCRUDSerializer


class StaffInfoView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = StaffSerializer

    def get(self, request):
        staff_profile = StaffProfile.objects.select_related('user', 'rank').get(user=request.user)
        serializer = self.serializer_class(staff_profile, context=self.get_renderer_context())
        return Response(serializer.data, status=status.HTTP_200_OK)


class StaffProfileFilter(filters.FilterSet):
    name = filters.CharFilter(method='filter_by_name_or_surname', label='Name or Surname')
    role = filters.NumberFilter(field_name='role')
    is_active = filters.BooleanFilter(field_name='user__is_active')

    class Meta:
        model = StaffProfile
        fields = ['name', 'role', 'is_active']

    def filter_by_name_or_surname(self, queryset, name, value):
        return queryset.filter(Q(name__icontains=value) | Q(surname__icontains=value))


class StaffModelViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsDirectorAndTechnologist]
    queryset = StaffProfile.objects.select_related('user', 'rank')
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = StaffProfileFilter

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return StaffSerializer
        return StaffCreateUpdateSerializer

    @extend_schema(request=StaffCreateUpdateSerializer, responses=StaffSerializer)
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user_data = {
            'username': serializer.validated_data.pop('username'),
            'password': serializer.validated_data.pop('password'),
            'status': UserStatus.STAFF
        }
        user_serializer = MyUserCreateSerializer(data=user_data)
        user_serializer.is_valid(raise_exception=True)
        user = MyUser.objects.create_user(**user_data)

        staff_profile = StaffProfile.objects.create(user=user, **serializer.validated_data)
        serializer = StaffSerializer(staff_profile, context=self.get_renderer_context())

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @extend_schema(request=StaffCreateUpdateSerializer, responses=StaffSerializer)
    def update(self, request, *args, **kwargs):
        staff_profile = self.get_object()
        serializer = self.get_serializer(staff_profile, data=request.data)
        serializer.is_valid(raise_exception=True)

        user_data = {}
        if serializer.validated_data.get('username'):
            user_data['username'] = serializer.validated_data.get('username')
        if serializer.validated_data.get('password'):
            user_data['password'] = serializer.validated_data.pop('password')

        if user_data:
            user_serializer = MyUserUpdateSerializer(data=user_data)
            user_serializer.is_valid(raise_exception=True)
            user = user_serializer.update(staff_profile.user, user_serializer.data)
            user.set_password(user_data.get('password'))
            user.save()

        self.perform_update(serializer)
        serializer = StaffSerializer(staff_profile, context=self.get_renderer_context())
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(request=StaffCreateUpdateSerializer, responses=StaffSerializer)
    def partial_update(self, request, *args, **kwargs):
        staff_profile = self.get_object()
        serializer = self.get_serializer(staff_profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        user_data = {}
        if serializer.validated_data.get('username'):
            user_data['username'] = serializer.validated_data.get('username')
        if serializer.validated_data.get('password'):
            user_data['password'] = serializer.validated_data.pop('password')

        if user_data:
            user_serializer = MyUserUpdateSerializer(data=user_data)
            user_serializer.is_valid(raise_exception=True)
            user = user_serializer.update(staff_profile.user, user_serializer.data)
            user.set_password(user_data.get('password'))
            user.save()

        self.perform_update(serializer)
        serializer = StaffSerializer(staff_profile, context=self.get_renderer_context())
        return Response(serializer.data, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        staff_profile = self.get_object()
        user = staff_profile.user
        user.is_active = False
        user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ClientProfileFilter(filters.FilterSet):
    name = filters.CharFilter(method='filter_by_all_fields', label='Name, Surname or Company Title')
    is_active = filters.BooleanFilter(field_name='user__is_active')

    class Meta:
        model = ClientProfile
        fields = ['name', 'is_active']

    def filter_by_all_fields(self, queryset, name, value):
        return queryset.filter(
            Q(name__icontains=value) | Q(company_title__icontains=value) | Q(surname__icontains=value)
        )


class ClientModelViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsDirectorAndTechnologist]
    queryset = ClientProfile.objects.select_related('user')
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = ClientProfileFilter

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return ClientSerializer
        return ClientCreateUpdateSerializer

    @extend_schema(request=ClientCreateUpdateSerializer, responses=ClientSerializer)
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user_data = {
            'username': serializer.validated_data.pop('username'),
            'password': serializer.validated_data.pop('password'),
            'status': UserStatus.CLIENT
        }
        user_serializer = MyUserCreateSerializer(data=user_data)
        user_serializer.is_valid(raise_exception=True)
        user = MyUser.objects.create_user(**user_data)

        client_profile = ClientProfile.objects.create(user=user, **serializer.validated_data)
        serializer = ClientSerializer(client_profile, context=self.get_renderer_context())

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @extend_schema(request=ClientCreateUpdateSerializer, responses=ClientSerializer)
    def update(self, request, *args, **kwargs):
        client_profile = self.get_object()
        serializer = self.get_serializer(client_profile, data=request.data)
        serializer.is_valid(raise_exception=True)

        user_data = {}
        if serializer.validated_data.get('username'):
            user_data['username'] = serializer.validated_data.get('username')
        if serializer.validated_data.get('password'):
            user_data['password'] = serializer.validated_data.pop('password')

        if user_data:
            user_serializer = MyUserUpdateSerializer(data=user_data)
            user_serializer.is_valid(raise_exception=True)
            user = user_serializer.update(client_profile.user, user_serializer.data)
            user.set_password(user_data.get('password'))
            user.save()

        self.perform_update(serializer)
        serializer = ClientSerializer(client_profile, context=self.get_renderer_context())
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(request=ClientCreateUpdateSerializer, responses=ClientSerializer)
    def partial_update(self, request, *args, **kwargs):
        client_profile = self.get_object()
        serializer = self.get_serializer(client_profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        user_data = {}
        if serializer.validated_data.get('username'):
            user_data['username'] = serializer.validated_data.get('username')
        if serializer.validated_data.get('password'):
            user_data['password'] = serializer.validated_data.pop('password')

        if user_data:
            user_serializer = MyUserUpdateSerializer(data=user_data)
            user_serializer.is_valid(raise_exception=True)
            user = user_serializer.update(client_profile.user, user_serializer.data)
            user.set_password(user_data.get('password'))
            user.save()

        self.perform_update(serializer)
        serializer = ClientSerializer(client_profile, context=self.get_renderer_context())
        return Response(serializer.data, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        client_profile = self.get_object()
        user = client_profile.user
        user.is_active = False
        user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ClientListView(ListAPIView):
    permission_classes = [IsAuthenticated, IsDirectorAndTechnologist]
    queryset = ClientProfile.objects.all()
    serializer_class = ClientListSerializer


class ClientFileCRUDView(APIView):
    permission_classes = [IsAuthenticated, IsDirectorAndTechnologist]

    @extend_schema(
        request=ClientFileCRUDSerializer,
        responses={200: {'type': 'object', 'properties': {'text': {'type': 'string'}}}}
    )
    def post(self, request):
        serializer = ClientFileCRUDSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        client_id = serializer.validated_data.get('client_id')
        files = request.FILES.getlist('files')
        delete_ids = serializer.validated_data.get('delete_ids', [])

        create_data = [ClientFile(client_id=client_id, file=file) for file in files]
        ClientFile.objects.bulk_create(create_data)

        if delete_ids:
            ClientFile.objects.filter(id__in=delete_ids).delete()

        return Response({"text": "Success!"}, status=status.HTTP_200_OK)