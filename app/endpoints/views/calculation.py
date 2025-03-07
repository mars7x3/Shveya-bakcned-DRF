from django.db.models import Q
from rest_framework import status, mixins
from rest_framework.generics import RetrieveAPIView, ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet, GenericViewSet
from django_filters import rest_framework as filters
from endpoints.pagination import StandardPagination
from endpoints.permissions import IsDirectorAndTechnologist, IsStaff
from my_db.enums import NomType
from my_db.models import Operation, Nomenclature, Calculation, StaffProfile, ClientProfile
from serializers.calculation import OperationDetailSerializer, ConsumableDetailSerializer, CalculationSerializer, \
    CalculationListSerializer


class OperationTitleListView(APIView):
    permission_classes = [IsAuthenticated, IsDirectorAndTechnologist]

    def get(self, request):
        operations = list(Operation.objects.filter(is_active=True).values('id', 'title'))
        return Response(operations, status=status.HTTP_200_OK)


class OperationDetailView(RetrieveAPIView):
    permission_classes = [IsAuthenticated, IsDirectorAndTechnologist]
    queryset = Operation.objects.filter(is_active=True)
    serializer_class = OperationDetailSerializer


class ConsumableTitleListView(APIView):
    permission_classes = [IsAuthenticated, IsStaff]

    def get(self, request):
        operations = list(Nomenclature.objects.filter(
            is_active=True, type=NomType.MATERIAL).values('id', 'title')
                          )
        return Response(operations, status=status.HTTP_200_OK)


class ConsumableDetailView(RetrieveAPIView):
    permission_classes = [IsAuthenticated, IsStaff]
    queryset = Nomenclature.objects.filter(is_active=True)
    serializer_class = ConsumableDetailSerializer


class CalculationViewSet(mixins.CreateModelMixin,
                   mixins.RetrieveModelMixin,
                   mixins.UpdateModelMixin,
                   mixins.DestroyModelMixin,
                   GenericViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = CalculationSerializer
    queryset = Calculation.objects.all()


class CalculationListFilter(filters.FilterSet):
    title = filters.CharFilter(lookup_expr="icontains")
    created_at = filters.DateFromToRangeFilter()

    class Meta:
        model = Calculation
        fields = ['title', 'created_at']


class CalculationListView(ListAPIView):
    permission_classes = [IsAuthenticated, IsDirectorAndTechnologist]
    queryset = Calculation.objects.all()
    serializer_class = CalculationListSerializer
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = CalculationListFilter
    pagination_class = StandardPagination


class ClientNameListView(APIView):
    permission_classes = [IsAuthenticated, IsDirectorAndTechnologist]

    def get(self, request):
        clients = list(ClientProfile.objects.all().values('id', 'name', 'surname', 'company_title')
                          )
        return Response(clients, status=status.HTTP_200_OK)