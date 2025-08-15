from collections import defaultdict
from decimal import Decimal

from django.db.models import Q, Sum
from rest_framework import viewsets, mixins, status
from rest_framework.permissions import IsAuthenticated
from django_filters import rest_framework as filters
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet

from endpoints.pagination import StandardPagination
from endpoints.permissions import IsDirectorAndTechnologist, ClientIsOwner
from my_db.models import Order, NomCount
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
    permission_classes = [IsAuthenticated, IsDirectorAndTechnologist]

    def get(self, request):
        order_id = request.query_params.get('order_id')
        invoice = defaultdict(lambda: {
            'colors_need': defaultdict(Decimal),   # расход по цветам
            'colors_stock': defaultdict(Decimal),  # остатки по цветам
            'unit': None,
            'title': None
        })

        order = Order.objects.prefetch_related(
            'products__amounts__color',
            'products__nomenclature__consumables__material_nomenclature__color',
        ).get(id=order_id)

        material_ids = set()
        for order_product in order.products.all():
            product_nomenclature = order_product.nomenclature
            consumables = product_nomenclature.consumables.all()

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
                    invoice[key]['colors_need'][color_title] += total_consumed

                    material_ids.add(material.id)

        # Остатки по цветам из NomCount.nomenclature.color
        stocks = (
            NomCount.objects
            .filter(nomenclature_id__in=material_ids)
            .values('nomenclature_id', 'nomenclature__color__title')
            .annotate(total_stock=Sum('amount'))
        )

        for stock in stocks:
            mat_id = stock['nomenclature_id']
            color_title = stock['nomenclature__color__title'] or '—'
            invoice[mat_id]['colors_stock'][color_title] += stock['total_stock'] or Decimal(0)

        # Формируем результат
        result = []
        for entry in invoice.values():
            colors_dict = {}
            # теперь берём только цвета, которые есть в заказе
            for color in entry['colors_need'].keys():
                colors_dict[color] = {
                    'need': float(entry['colors_need'][color]),
                    'stock': float(entry['colors_stock'].get(color, Decimal(0)))
                }

            result.append({
                'title': entry['title'],
                'colors': colors_dict,
                'unit': entry['unit']
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