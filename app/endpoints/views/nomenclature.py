
from django.db.models import Q
from drf_spectacular.utils import extend_schema
from rest_framework.response import Response
from rest_framework import viewsets, mixins, status
from rest_framework.generics import ListAPIView, CreateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet

from endpoints.pagination import StandardPagination
from endpoints.permissions import IsStaff, IsDirectorAndTechnologist
from my_db.enums import NomType, NomStatus
from my_db.models import Nomenclature, Pattern, Combination, Operation, Equipment, EquipmentImages, EquipmentService, \
    NomFile, Warehouse
from serializers.nomenclature import GPListSerializer, GPDetailSerializer, PatternCRUDSerializer, \
    CombinationCRUDSerializer, GPCRUDSerializer, OperationCRUDSerializer, EquipmentSerializer, MaterialListSerializer, \
    PatternSerializer, ProductListSerializer, CombinationSerializer, EquipmentImageCRUDSerializer, \
    EquipmentListSerializer, EquipmentServiceSerializer, EquipmentServiceReadSerializer, EquipmentCRUDSerializer, \
    OperationRetrieveSerializer, FilesCRUDSerializer, FileSerializer
from django_filters import rest_framework as filters


class GPListFilter(filters.FilterSet):
    title = filters.CharFilter(method='filter_by_title', label='Product title or vendor code')

    class Meta:
        model = Nomenclature
        fields = ['title', 'is_active']

    def filter_by_title(self, queryset, name, value):
        return queryset.filter(Q(title__icontains=value) | Q(vendor_code__icontains=value))


class GPListView(ListAPIView):
    permission_classes = [IsAuthenticated, IsStaff]
    queryset = Nomenclature.objects.filter(type=NomType.GP)
    serializer_class = GPListSerializer
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = GPListFilter
    pagination_class = StandardPagination


class MaterialListView(ListAPIView):
    permission_classes = [IsAuthenticated, IsStaff]
    queryset = Nomenclature.objects.filter(type=NomType.MATERIAL)
    serializer_class = MaterialListSerializer
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = GPListFilter


class MaterialListMyView(ListAPIView):
    permission_classes = [IsAuthenticated, IsStaff]
    queryset = Nomenclature.objects.all()
    serializer_class = MaterialListSerializer
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = GPListFilter

    def get_queryset(self):
        staff = self.request.user.staff_profile
        product_id = self.request.query_params.get('product')
        warehouse = Warehouse.objects.filter(staffs=staff).first()
        product = Nomenclature.objects.get(id=product_id)
        titles = product.consumables.filter(
            material_nomenclature__status=NomStatus.CUT
        ).values_list('material_nomenclature__title', flat=True)

        nomenclatures = Nomenclature.objects.filter(
            title__in=titles,
            counts__warehouse=warehouse,
            counts__amount__gt=0
        ).distinct()

        return nomenclatures


class GPModelViewSet(mixins.CreateModelMixin,
                   mixins.UpdateModelMixin,
                   mixins.DestroyModelMixin,
                   GenericViewSet):
    permission_classes = [IsAuthenticated, IsDirectorAndTechnologist]
    queryset = Nomenclature.objects.all()
    serializer_class = GPCRUDSerializer


class GPDetailView(APIView):
    permission_classes = [IsAuthenticated, IsDirectorAndTechnologist]

    def get_object(self, pk):
        try:
            return Nomenclature.objects.prefetch_related(
                'combinations',
                'prices',
                'consumables'
            ).get(id=pk)
        except:
            return None

    @extend_schema(responses=GPDetailSerializer)
    def get(self, request, pk):
        product = self.get_object(pk)
        if not product:
            return Response({'error': 'Product does not exist!'}, status=status.HTTP_404_NOT_FOUND)

        serializer = GPDetailSerializer(product)
        return Response(serializer.data)


class PatternListView(APIView):
    permission_classes = [IsAuthenticated, IsDirectorAndTechnologist]

    @staticmethod
    def get_object(self, pk):
        try:
            return Nomenclature.objects.prefetch_related('patterns').get(pk=pk)
        except:
            return Response('Product does not exist!', status=status.HTTP_404_NOT_FOUND)

    @extend_schema(
        responses=PatternSerializer(many=True),
    )
    def get(self, request, pk):
        product = self.get_object(pk)
        patterns = product.patterns.all()
        serializer = PatternSerializer(patterns, many=True, context=self.get_renderer_context())
        return Response(serializer.data)


class FileListView(APIView):
    permission_classes = [IsAuthenticated, IsDirectorAndTechnologist]

    def get_object(self, pk):
        try:
            return Nomenclature.objects.prefetch_related('files').get(pk=pk)
        except:
            return Response('Product does not exist!', status=status.HTTP_404_NOT_FOUND)

    @extend_schema(
        responses=FileSerializer(many=True),
    )
    def get(self, request, pk):
        product = self.get_object(pk)
        files = product.files.all()
        serializer = FileSerializer(files, many=True, context=self.get_renderer_context())
        return Response(serializer.data)


class PatternCRUDView(APIView):
    permission_classes = [IsAuthenticated, IsDirectorAndTechnologist]

    @extend_schema(
        request=PatternCRUDSerializer,
        responses={200: {'type': 'object', 'properties': {'text': {'type': 'string'}}}}
    )
    def post(self, request):
        serializer = PatternCRUDSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        product_id = serializer.validated_data.get('product_id')
        images = request.FILES.getlist('images')
        delete_ids = serializer.validated_data.get('delete_ids', [])

        create_data = [Pattern(nomenclature_id=product_id, image=image) for image in images]
        Pattern.objects.bulk_create(create_data)

        if delete_ids:
            Pattern.objects.filter(id__in=delete_ids).delete()

        return Response({"text": "Success!"}, status=status.HTTP_200_OK)


class FileCRUDView(APIView):
    permission_classes = [IsAuthenticated, IsDirectorAndTechnologist]

    @extend_schema(
        request=FilesCRUDSerializer,
        responses={200: {'type': 'object', 'properties': {'text': {'type': 'string'}}}}
    )
    def post(self, request):
        serializer = FilesCRUDSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        product_id = serializer.validated_data.get('product_id')
        files = request.FILES.getlist('files')
        delete_ids = serializer.validated_data.get('delete_ids', [])

        create_data = [NomFile(nomenclature_id=product_id, file=file) for file in files]
        NomFile.objects.bulk_create(create_data)

        if delete_ids:
            NomFile.objects.filter(id__in=delete_ids).delete()

        return Response({"text": "Success!"}, status=status.HTTP_200_OK)


@extend_schema(request=CombinationCRUDSerializer, responses=CombinationSerializer)
class CombinationModelViewSet(mixins.CreateModelMixin,
                   mixins.UpdateModelMixin,
                   mixins.DestroyModelMixin,
                   GenericViewSet):
    permission_classes = [IsAuthenticated, IsDirectorAndTechnologist]
    queryset = Combination.objects.all()
    serializer_class = CombinationCRUDSerializer


class OperationListFilter(filters.FilterSet):
    title = filters.CharFilter(field_name="title", lookup_expr="icontains")

    class Meta:
        model = Operation
        fields = ['title']


class OperationModelViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsDirectorAndTechnologist]
    queryset = Operation.objects.all()
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = OperationListFilter
    pagination_class = StandardPagination

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return OperationRetrieveSerializer
        return OperationCRUDSerializer

    def get_queryset(self):
        if self.action == 'retrieve':
            return Operation.objects.select_related('nomenclature', 'rank')
        return Operation.objects.all()


class EquipmentModelViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsDirectorAndTechnologist]
    queryset = Equipment.objects.all()
    serializer_class = EquipmentSerializer

    def get_serializer_class(self):
        if self.action == 'list':
            return EquipmentListSerializer
        if self.request.method in ['POST', 'PATCH', "PUT"]:
            return EquipmentCRUDSerializer
        return super().get_serializer_class()

    def get_queryset(self):
        if self.action == 'retrieve':
            return Equipment.objects.prefetch_related('images', 'services')
        return Equipment.objects.all()


class EquipmentImageCRUDView(APIView):
    permission_classes = [IsAuthenticated, IsDirectorAndTechnologist]

    @extend_schema(
        request=EquipmentImageCRUDSerializer,
        responses={200: {'type': 'object', 'properties': {'text': {'type': 'string'}}}}
    )
    def post(self, request):
        serializer = EquipmentImageCRUDSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        equipment_id = serializer.validated_data.get('equipment_id')
        images = request.FILES.getlist('images')

        delete_ids = serializer.validated_data.get('delete_ids', [])

        create_data = [EquipmentImages(equipment_id=equipment_id, image=image) for image in images]
        EquipmentImages.objects.bulk_create(create_data)

        if delete_ids:
            EquipmentImages.objects.filter(id__in=delete_ids).delete()

        return Response({"text": "Success!"}, status=status.HTTP_200_OK)


class EquipmentServiceView(CreateAPIView):
    permission_classes = [IsAuthenticated, IsDirectorAndTechnologist]
    queryset = EquipmentService.objects.all()
    serializer_class = EquipmentServiceSerializer


class ProductListView(ListAPIView):
    permission_classes = [IsAuthenticated, IsDirectorAndTechnologist]
    queryset = (
        Nomenclature.objects
                .prefetch_related('operations')
                .filter(is_active=True, type=NomType.GP)
    )
    serializer_class = ProductListSerializer



