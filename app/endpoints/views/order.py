from email.policy import default

from django.db.models import Q, Sum, ExpressionWrapper, F, FloatField
from rest_framework import viewsets, mixins
from rest_framework.generics import ListAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from django_filters import rest_framework as filters
from rest_framework.viewsets import GenericViewSet

from endpoints.pagination import StandardPagination
from endpoints.permissions import IsDirectorAndTechnologist
from my_db.enums import WorkStatus
from my_db.models import Order
from serializers.order import OrderSerializer, OrderCRUDSerializer


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


class OrderListView(ListAPIView):
    permission_classes = [IsAuthenticated, IsDirectorAndTechnologist]
    queryset = Order.objects.annotate(
        total_products=Sum('products__amounts__amount'),
        completed_products=Sum(
            'products__nomenclature__operations__details__amount',
            filter=Q(products__nomenclature__operations__details__work__status=WorkStatus.DONE),
            default=0
        ),
        total_cost=Sum(F('products__nomenclature__cost_price') * F('products__amounts__amount'),
                       output_field=FloatField(), default=0),
        total_revenue=Sum(F('products__price') * F('products__amounts__amount'), output_field=FloatField()),
        completion_percentage=ExpressionWrapper(
            (Sum(
                'products__nomenclature__operations__details__amount',
                filter=Q(products__nomenclature__operations__details__work__status=WorkStatus.DONE), default=0
            ) * 100.0 / Sum('products__amounts__amount', default=0)),
            output_field=FloatField()
        ),
    )
    serializer_class = OrderSerializer
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = OrderFilter
    pagination_class = StandardPagination


class OrderModelViewSet(mixins.CreateModelMixin,
                   mixins.RetrieveModelMixin,
                   mixins.UpdateModelMixin,
                   mixins.DestroyModelMixin,
                   GenericViewSet):

    permission_classes = [IsAuthenticated, IsDirectorAndTechnologist]
    queryset = Order.objects.select_related('client')
    serializer_class = OrderCRUDSerializer
