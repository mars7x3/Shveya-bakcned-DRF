from rest_framework import viewsets, mixins
from rest_framework.permissions import IsAuthenticated
from django_filters import rest_framework as filters
from rest_framework.views import APIView

from endpoints.pagination import StandardPagination
from endpoints.permissions import IsDirectorAndTechnologist
from my_db.models import CombinationFile, Combination, Operation
from serializers.sample import CombinationFileCRUDSerializer, CombinationFileDetailSerializer, \
    CombinationListSerializer, CombinationDetailSerializer, OperationDetailSerializer, OperationListSerializer


class CombinationFileCRUDVIew(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsDirectorAndTechnologist]
    queryset = CombinationFile.objects.all()
    serializer_class = CombinationFileCRUDSerializer

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return CombinationFileDetailSerializer
        return CombinationFileCRUDSerializer

    def get_queryset(self):
        queryset = CombinationFile.objects.all()
        if self.action == 'retrieve':
            return queryset.prefetch_related('combinations')
        return queryset


class CombinationListFilter(filters.FilterSet):
    title = filters.CharFilter(field_name="title", lookup_expr="icontains")

    class Meta:
        model = Combination
        fields = ['title']


class SampleCombinationListView(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated, IsDirectorAndTechnologist]
    queryset = Combination.objects.filter(is_sample=True).select_related('file')
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = CombinationListFilter
    pagination_class = StandardPagination

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return CombinationDetailSerializer
        return CombinationListSerializer

    def get_queryset(self):
        queryset = Combination.objects.filter(is_sample=True).select_related('file')
        if self.action == 'retrieve':
            return queryset.prefetch_related('operations')
        return queryset


class OperationListFilter(filters.FilterSet):
    title = filters.CharFilter(field_name="title", lookup_expr="icontains")

    class Meta:
        model = Operation
        fields = ['title']


class SampleOperationListView(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated, IsDirectorAndTechnologist]
    queryset = Operation.objects.filter(is_sample=True)
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = OperationListFilter
    pagination_class = StandardPagination

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return OperationDetailSerializer
        return OperationListSerializer

    def get_queryset(self):
        queryset = Operation.objects.filter(is_sample=True)
        if self.action == 'retrieve':
            return queryset.select_related('equipment', 'rank')
        return queryset


