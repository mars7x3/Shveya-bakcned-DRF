from collections import defaultdict
from decimal import Decimal

from django.db.models import Q
from rest_framework import viewsets, mixins, status
from rest_framework.permissions import IsAuthenticated
from django_filters import rest_framework as filters
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet

from endpoints.pagination import StandardPagination
from endpoints.permissions import IsDirectorAndTechnologist, ClientIsOwner
from my_db.models import Order
from serializers.order import OrderListSerializer, OrderCRUDSerializer, OrderDetailSerializer, \
    ClientOrderListSerializer, ClientOrderDetailSerializer


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


class InvoiceDataVie(APIView):
    def get(self, request):
        order_id = request.query_params.get('order_id')
        invoice = defaultdict(lambda: {'colors': defaultdict(Decimal), 'unit': None, 'title': None})

        order = Order.objects.prefetch_related(
            'products__amounts__color',
            'products__nomenclature__consumables__material_nomenclature',
        ).get(id=order_id)

        for order_product in order.products.all():
            product_nomenclature = order_product.nomenclature
            consumables = product_nomenclature.consumables.all()

            # Для каждого OrderProductAmount (может быть разный цвет/размер)
            for amount_entry in order_product.amounts.all():
                amount = amount_entry.amount
                color_title = amount_entry.color.title if amount_entry.color else '—'

                for consumable in consumables:
                    material = consumable.material_nomenclature
                    if not material:
                        continue

                    total_consumed = amount * consumable.consumption

                    key = material.id
                    invoice[key]['title'] = material.title
                    invoice[key]['unit'] = consumable.unit
                    invoice[key]['colors'][color_title] += total_consumed

        # Формируем итоговый список
        result = []
        for entry in invoice.values():
            result.append({
                'title': entry['title'],
                'colors': {color: float(amount) for color, amount in entry['colors'].items()},
                'unit': entry['unit'],
            })

        return Response(result, status=status.HTTP_200_OK)


class ClientOrdersView(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated, ClientIsOwner]
    queryset = Order.objects.all()
    pagination_class = StandardPagination

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ClientOrderDetailSerializer
        return ClientOrderListSerializer

    def get_queryset(self):
        client = self.request.user.client_profile
        return Order.objects.filter(client=client)