from django.db.models import Q, Subquery, OuterRef
from drf_spectacular.utils import extend_schema
from rest_framework import viewsets, status, mixins
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters import rest_framework as filters
from rest_framework.viewsets import GenericViewSet
from yaml.serializer import Serializer

from endpoints.pagination import StandardPagination
from endpoints.permissions import IsDirectorAndTechnologist
from my_db.enums import NomType
from my_db.models import Warehouse, Nomenclature, NomCount
from serializers.warehouse import WarehouseSerializer, WarehouseCRUDSerializer, MaterialSerializer, \
    MaterialCRUDSerializer


class WarehouseModelViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsDirectorAndTechnologist]
    queryset = Warehouse.objects.prefetch_related('staffs')

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return WarehouseCRUDSerializer
        return WarehouseSerializer


class MaterialListFilter(filters.FilterSet):
    warehouse = filters.CharFilter(method='filter_by_warehouse', label='ID склада')
    is_active = filters.NumberFilter(field_name='is_active')
    title = filters.CharFilter(method='filter_by_title_vendor_code', label='Название или артикул')

    class Meta:
        model = Nomenclature
        fields = ['title', 'is_active', 'warehouse', 'vendor_code']

    def filter_by_warehouse(self, queryset, warehouse, value):
        return queryset.filter(counts__warehouse_id=value)

    def filter_by_title_vendor_code(self, queryset, title, value):
        return queryset.filter(
            Q(title__icontains=value) |
            Q(vendor_code__icontains=value)
        )


class WarehouseMaterialListView(ListAPIView):
    permission_classes = [IsAuthenticated, IsDirectorAndTechnologist]
    serializer_class = MaterialSerializer
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = MaterialListFilter
    pagination_class = StandardPagination

    def get_queryset(self):
        warehouse_id = self.request.query_params.get('warehouse')

        if warehouse_id:
            return Nomenclature.objects.filter(type=NomType.MATERIAL).annotate(
                filtered_count_amount=Subquery(
                    NomCount.objects.filter(
                        nomenclature=OuterRef('pk'),
                        warehouse_id=warehouse_id
                    ).values('amount')[:1]
                )
            )
        else:
            return Nomenclature.objects.filter(type=NomType.MATERIAL)


class MaterialModelViewSet(mixins.CreateModelMixin,
                   mixins.RetrieveModelMixin,
                   mixins.UpdateModelMixin,
                   mixins.DestroyModelMixin,
                   GenericViewSet):
    permission_classes = [IsAuthenticated, IsDirectorAndTechnologist]
    queryset = Nomenclature.objects.filter(type=NomType.MATERIAL)
    serializer_class = MaterialCRUDSerializer


