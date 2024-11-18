from tracemalloc import Trace

from django.db import transaction
from django.db.models import Q, Subquery, OuterRef, F
from django.template.defaulttags import comment
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
from endpoints.permissions import IsDirectorAndTechnologist, IsWarehouse
from my_db.enums import NomType, QuantityStatus
from my_db.models import Warehouse, Nomenclature, NomCount, Quantity, QuantityHistory, QuantityNomenclature, \
    QuantityFile
from serializers.warehouse import WarehouseSerializer, WarehouseCRUDSerializer, MaterialSerializer, \
    MaterialCRUDSerializer, StockInputSerializer, StockOutputSerializer, StockDefectiveSerializer, \
    StockDefectiveFileSerializer, StockOutputUpdateSerializer


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


class StockInputView(APIView):
    permission_classes = [IsAuthenticated, IsWarehouse]

    @extend_schema(request=StockInputSerializer(many=True))
    def post(self, request):
        staff = request.user.staff_profile
        data = request.data

        quantity = Quantity.objects.create(in_warehouse=staff.warehouses.first(), status=QuantityStatus.ACTIVE)

        create_data = []
        for i in data:
            create_data.append(
                QuantityNomenclature(
                    quantity=quantity,
                    nomenclature_id=i['product_id'],
                    amount=i['amount'],
                    price=i['price']
                )
            )
        QuantityNomenclature.objects.bulk_create(create_data)

        QuantityHistory.objects.create(quantity=quantity, staff_id=staff.id, staff_name=staff.name,
                                       staff_surname=staff.surname, status=quantity.status)

        with transaction.atomic():
            for item in data:
                obj, created = NomCount.objects.get_or_create(
                    warehouse=quantity.in_warehouse,
                    nomenclature_id=item["product_id"],
                )
                if not created:
                    obj.amount += item["amount"]
                    obj.save()

        return Response('Success!', status=status.HTTP_200_OK)


class StockOutputView(APIView):
    permission_classes = [IsAuthenticated, IsWarehouse]

    @extend_schema(request=StockOutputSerializer())
    def post(self, request):
        staff = request.user.staff_profile
        data = request.data

        quantity = Quantity.objects.create(in_warehouse=data['output_warehouse_id'],
                                           out_warehouse_id=staff.warehouses.first(),
                                           status=QuantityStatus.PROGRESSING)

        create_data = []
        for i in data['products']:
            create_data.append(
                QuantityNomenclature(
                    quantity=quantity,
                    nomenclature_id=i['product_id'],
                    amount=i['amount'],
                )
            )
        QuantityNomenclature.objects.bulk_create(create_data)

        QuantityHistory.objects.create(quantity=quantity, staff_id=staff.id, staff_name=staff.name,
                                       staff_surname=staff.surname, status=quantity.status)

        return Response('Success!', status=status.HTTP_200_OK)


class StockDefectiveView(APIView):
    permission_classes = [IsAuthenticated, IsWarehouse]

    @extend_schema(request=StockDefectiveSerializer())
    def post(self, request):
        staff = request.user.staff_profile
        data = request.data

        quantity = Quantity.objects.create(out_warehouse=staff.warehouses.first(), status=QuantityStatus.ACTIVE,
                                           comment=data['comment'])

        create_data = []
        for i in data['products']:
            create_data.append(
                QuantityNomenclature(
                    quantity=quantity,
                    nomenclature_id=i['product_id'],
                    amount=i['amount'],
                )
            )
        QuantityNomenclature.objects.bulk_create(create_data)

        QuantityHistory.objects.create(quantity=quantity, staff_id=staff.id, staff_name=staff.name,
                                       staff_surname=staff.surname, status=quantity.status)

        updates = []
        for item in data:
            updates.append({
                "nomenclature_id": item["product_id"],
                "amount": item["amount"]
            })

        with transaction.atomic():
            for update in updates:
                NomCount.objects.filter(
                    warehouse=staff.warehouses.first(),
                    nomenclature_id=update["nomenclature_id"]
                ).update(amount=F('amount') - update["amount"])

        return Response('Success!', status=status.HTTP_200_OK)


class StockDefectiveFileView(APIView):
    permission_classes = [IsAuthenticated, IsWarehouse]

    @extend_schema(request=StockDefectiveFileSerializer())
    def post(self, request):
        files = request.FILES.getlist('files')

        create_data = []
        for i in files:
            create_data.append(
                QuantityFile(
                    quantity_id=request.data['quantity_id'],
                    file=i
                )
            )
        QuantityFile.objects.bulk_create(create_data)

        return Response('Success!', status=status.HTTP_200_OK)


class StockOutputUpdateView(APIView):
    permission_classes = [IsAuthenticated, IsWarehouse]

    @extend_schema(request=StockOutputUpdateSerializer())
    def post(self, request):
        staff = request.user.staff_profile

        quantity = Quantity.objects.get(id=request.data['quantity_id'])
        quantity.status = request.data['status']
        quantity.save()

        QuantityHistory.objects.create(quantity=quantity, staff_id=staff.id, staff_name=staff.name,
                                       staff_surname=staff.surname, status=quantity.status)

        updates = quantity.quantities.all()
        if quantity.status == QuantityStatus.ACTIVE:
            with transaction.atomic():
                for update in updates:
                    NomCount.objects.filter(
                        warehouse=quantity.out_warehouse,
                        nomenclature=update.nomenclature
                    ).update(amount=F('amount') - update.amount)

            with transaction.atomic():
                for update in updates:
                    NomCount.objects.filter(
                        warehouse=quantity.in_warehouse,
                        nomenclature=update.nomenclature
                    ).update(amount=F('amount') + update.amount)

        return Response('Success!', status=status.HTTP_200_OK)