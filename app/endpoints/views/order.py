from email.policy import default

from django.db.models import Q, Sum, ExpressionWrapper, F, FloatField
from rest_framework import viewsets, mixins
from rest_framework.generics import ListAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from django_filters import rest_framework as filters
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet

from endpoints.pagination import StandardPagination
from endpoints.permissions import IsDirectorAndTechnologist
from my_db.models import Order
from serializers.order import OrderListSerializer, OrderCRUDSerializer, OrderDetailSerializer


class OrderFilter(filters.FilterSet):
    name = filters.CharFilter(method='filter_by_name_or_surname', label='Name, Surname or Company Title')
    status = filters.NumberFilter(field_name='status')

    class Meta:
        model = Order
        fields = ['name', 'status']

    def filter_by_name_or_surname(self, queryset, name, value):
        return queryset.filter(
            Q(client__name__icontains=value) |
            Q(client__surname__icontains=value) |
            Q(client__company_title__icontains=value))


class OrderReadView(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated, IsDirectorAndTechnologist]
    queryset = Order.objects.all()
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = OrderFilter
    pagination_class = StandardPagination

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return OrderDetailSerializer
        return OrderListSerializer

    def get_queryset(self):
        if self.action == 'retrieve':
            return Order.objects.all().prefetch_related('parties__details__size', 'parties__details__color',
                                                        'products__amounts__size', 'products__amounts__color')
        return Order.objects.all()


class OrderModelViewSet(mixins.CreateModelMixin,
                   mixins.UpdateModelMixin,
                   mixins.DestroyModelMixin,
                   GenericViewSet):

    permission_classes = [IsAuthenticated, IsDirectorAndTechnologist]
    queryset = Order.objects.select_related('client')
    serializer_class = OrderCRUDSerializer


