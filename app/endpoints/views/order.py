from collections import defaultdict
from decimal import Decimal

from django.core.exceptions import ObjectDoesNotExist
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


class InvoiceDataView(APIView):  # Исправлена опечатка в названии класса
    permission_classes = [IsAuthenticated, IsDirectorAndTechnologist]

    def get(self, request):
        order_id = request.query_params.get('order_id')

        # Валидация входных данных
        if not order_id:
            return Response(
                {'error': 'order_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            invoice_data = self._calculate_invoice_data(order_id)
            return Response(invoice_data, status=status.HTTP_200_OK)
        except ObjectDoesNotExist:
            return Response(
                {'error': 'Order not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': 'Internal server error'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _calculate_invoice_data(self, order_id):
        """Основная логика расчёта данных инвойса"""
        # Получаем заказ с оптимизированными запросами
        order = self._get_order_with_relations(order_id)

        # Рассчитываем потребности в материалах
        invoice, material_ids = self._calculate_material_needs(order)

        # Получаем остатки материалов
        self._add_material_stocks(invoice, material_ids)

        # Формируем результат
        return self._format_result(invoice)

    def _get_order_with_relations(self, order_id):
        """Получение заказа с предзагрузкой всех связанных данных"""
        return Order.objects.select_related().prefetch_related(
            'products__amounts__color',
            'products__nomenclature__consumables__material_nomenclature__color',
        ).get(id=order_id)

    def _calculate_material_needs(self, order):
        """Расчёт потребностей в материалах по цветам"""
        invoice = defaultdict(lambda: {
            'colors_need': defaultdict(Decimal),
            'colors_stock': defaultdict(Decimal),
            'unit': None,
            'title': None
        })
        material_ids = set()

        for order_product in order.products.all():
            consumables = order_product.nomenclature.consumables.select_related(
                'material_nomenclature'
            ).all()

            if not consumables:
                continue

            for amount_entry in order_product.amounts.select_related('color').all():
                amount = amount_entry.amount
                color_title = self._get_color_title(amount_entry.color)

                for consumable in consumables:
                    material = consumable.material_nomenclature
                    if not material:
                        continue

                    self._add_material_consumption(
                        invoice, material, consumable, amount, color_title
                    )
                    material_ids.add(material.id)

        return invoice, material_ids

    def _get_color_title(self, color):
        """Получение названия цвета с fallback"""
        return color.title if color else '—'

    def _add_material_consumption(self, invoice, material, consumable, amount, color_title):
        """Добавление расхода материала в инвойс"""
        total_consumed = amount * consumable.consumption
        key = material.id

        invoice[key]['title'] = material.title
        invoice[key]['unit'] = consumable.unit
        invoice[key]['colors_need'][color_title] += total_consumed

    def _add_material_stocks(self, invoice, material_ids):
        """Добавление остатков материалов по цветам"""
        if not material_ids:
            return

        stocks = (
            NomCount.objects
            .filter(nomenclature_id__in=material_ids)
            .select_related('nomenclature__color')
            .values('nomenclature_id', 'nomenclature__color__title')
            .annotate(total_stock=Sum('amount'))
        )

        for stock in stocks:
            mat_id = stock['nomenclature_id']
            color_title = stock['nomenclature__color__title'] or '—'
            stock_amount = stock['total_stock'] or Decimal(0)

            invoice[mat_id]['colors_stock'][color_title] += stock_amount

    def _format_result(self, invoice):
        """Форматирование результата для API ответа"""
        result = []

        for entry in invoice.values():
            if not entry['title']:  # Пропускаем пустые записи
                continue

            colors_dict = self._format_colors_data(entry)

            result.append({
                'title': entry['title'],
                'colors': colors_dict,
                'unit': entry['unit']
            })

        return sorted(result, key=lambda x: x['title'])  # Сортируем по названию

    def _format_colors_data(self, entry):
        """Форматирование данных по цветам"""
        colors_dict = {}

        for color in entry['colors_need'].keys():
            need_amount = entry['colors_need'][color]
            stock_amount = entry['colors_stock'].get(color, Decimal(0))

            colors_dict[color] = {
                'need': float(need_amount),
                'stock': float(stock_amount),
                'shortage': max(0, float(need_amount - stock_amount))  # Дефицит
            }

        return colors_dict


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