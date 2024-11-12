from tracemalloc import Trace

from django.http import Http404
from drf_spectacular.utils import extend_schema
from rest_framework.response import Response
from rest_framework import viewsets, mixins, status
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet

from endpoints.pagination import StandardPagination
from endpoints.permissions import IsStaff, IsDirectorAndTechnologist
from my_db.enums import NomType
from my_db.models import Nomenclature, Pattern, Combination, Operation, Equipment
from serializers.nomenclature import GPListSerializer, GPDetailSerializer, PatternCRUDSerializer, \
    CombinationCRUDSerializer, GPCRUDSerializer, OperationCRUDSerializer, EquipmentSerializer, MaterialListSerializer, \
    PatternSerializer, ProductListSerializer
from django_filters import rest_framework as filters


class GPListFilter(filters.FilterSet):
    class Meta:
        model = Nomenclature
        fields = ['title', 'is_active']


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
            return Nomenclature.objects.prefetch_related('operations', 'patterns', 'combinations').get(pk=pk)
        except:
            return Response('Product does not exist!', status=status.HTTP_404_NOT_FOUND)

    @extend_schema(
        responses=GPDetailSerializer,
    )
    def get(self, request, pk):
        product = self.get_object(pk)
        serializer = GPDetailSerializer(product)
        return Response(serializer.data)


class PatternListView(APIView):
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


class CombinationModelViewSet(mixins.CreateModelMixin,
                   mixins.UpdateModelMixin,
                   mixins.DestroyModelMixin,
                   GenericViewSet):
    permission_classes = [IsAuthenticated, IsDirectorAndTechnologist]
    queryset = Combination.objects.all()
    serializer_class = CombinationCRUDSerializer


class OperationModelViewSet(mixins.CreateModelMixin,
                   mixins.UpdateModelMixin,
                   mixins.DestroyModelMixin,
                   GenericViewSet):
    permission_classes = [IsAuthenticated, IsDirectorAndTechnologist]
    queryset = Operation.objects.all()
    serializer_class = OperationCRUDSerializer


class EquipmentModelViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsDirectorAndTechnologist]
    queryset = Equipment.objects.all()
    serializer_class = EquipmentSerializer


class ProductListView(ListAPIView):
    permission_classes = [IsAuthenticated, IsDirectorAndTechnologist]
    queryset = (
        Nomenclature.objects
                .select_related('category')
                .prefetch_related('category__sizes')
                .filter(is_active=True, type=NomType.GP)
    )
    serializer_class = ProductListSerializer

