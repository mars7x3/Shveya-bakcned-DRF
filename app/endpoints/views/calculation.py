
from rest_framework import status, mixins
from rest_framework.generics import RetrieveAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet, GenericViewSet

from endpoints.permissions import IsDirectorAndTechnologist
from my_db.enums import NomType
from my_db.models import Operation, Nomenclature, Calculation
from serializers.calculation import OperationDetailSerializer, ConsumableDetailSerializer, CalculationSerializer


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
    permission_classes = [IsAuthenticated, IsDirectorAndTechnologist]

    def get(self, request):
        operations = list(Nomenclature.objects.filter(
            is_active=True, type=NomType.MATERIAL).values('id', 'title')
                          )
        return Response(operations, status=status.HTTP_200_OK)


class ConsumableDetailView(RetrieveAPIView):
    permission_classes = [IsAuthenticated, IsDirectorAndTechnologist]
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
