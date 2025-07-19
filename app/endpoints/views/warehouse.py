
from django.db import transaction
from django.db.models import Q, Subquery, OuterRef, F, Prefetch, Value, DecimalField
from django.db.models.functions import Coalesce
from drf_spectacular.utils import extend_schema
from rest_framework import viewsets, status, mixins
from rest_framework.exceptions import ValidationError
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters import rest_framework as filters
from rest_framework.viewsets import GenericViewSet

from endpoints.pagination import StandardPagination
from endpoints.permissions import IsDirectorAndTechnologist, IsStaff
from my_db.enums import NomType, QuantityStatus, StaffRole, NomStatus
from my_db.models import Warehouse, Nomenclature, NomCount, Quantity, QuantityHistory, QuantityNomenclature, \
    QuantityFile
from serializers.warehouse import WarehouseSerializer, WarehouseCRUDSerializer, MaterialSerializer, \
    MaterialCRUDSerializer, StockInputSerializer, StockOutputSerializer, StockDefectiveSerializer, \
    StockDefectiveFileSerializer, StockOutputUpdateSerializer, MovingSerializer, MovingListSerializer, \
    MyMaterialsSerializer, WarehouseListSerializer, QuantityHistoryListSerializer, QuantityHistoryDetailSerializer, \
    CreateMaterialsSerializer


class WarehouseModelViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsDirectorAndTechnologist]
    queryset = Warehouse.objects.prefetch_related('staffs')

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return WarehouseCRUDSerializer
        return WarehouseSerializer


class MaterialListFilter(filters.FilterSet):
    warehouse = filters.CharFilter(method='filter_by_warehouse', label='ID склада')
    title = filters.CharFilter(method='filter_by_title_vendor_code', label='Название или артикул')

    class Meta:
        model = Nomenclature
        fields = ['title', 'is_active', 'warehouse', 'vendor_code', 'status']

    def filter_by_warehouse(self, queryset, warehouse, value):
        return queryset.filter(counts__warehouse_id=value)

    def filter_by_title_vendor_code(self, queryset, title, value):
        return queryset.filter(
            Q(title__icontains=value) |
            Q(vendor_code__icontains=value)
        )


class WarehouseMaterialListView(ListAPIView):
    permission_classes = [IsAuthenticated, IsStaff]
    serializer_class = MaterialSerializer
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = MaterialListFilter
    pagination_class = StandardPagination

    def get_queryset(self):
        warehouse_id = self.request.query_params.get('warehouse')

        base_qs = Nomenclature.objects.all()

        if warehouse_id:
            return base_qs.annotate(
                filtered_count_amount=Coalesce(
                    Subquery(
                        NomCount.objects.filter(
                            nomenclature=OuterRef('pk'),
                            warehouse_id=warehouse_id,
                        ).values('amount')[:1]
                    ),
                    Value(0),
                    output_field=DecimalField()
                )
            ).exclude(filtered_count_amount=0)

        return base_qs


class MyMaterialListView(ListAPIView):
    permission_classes = [IsAuthenticated, IsStaff]
    serializer_class = MyMaterialsSerializer
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = MaterialListFilter
    pagination_class = StandardPagination

    def get_queryset(self):
        manager = self.request.user.staff_profile
        warehouse = Warehouse.objects.filter(staffs=manager).first()
        queryset = Nomenclature.objects.prefetch_related(
            Prefetch(
                'counts',
                queryset=NomCount.objects.filter(warehouse=warehouse),
                to_attr='filtered_counts'
            )
        ).filter(
            counts__warehouse=warehouse,
            counts__amount__gt=0
        ).distinct()
        return queryset


class MaterialModelViewSet(mixins.CreateModelMixin,
                   mixins.RetrieveModelMixin,
                   mixins.UpdateModelMixin,
                   mixins.DestroyModelMixin,
                   GenericViewSet):
    permission_classes = [IsAuthenticated, IsStaff]
    queryset = Nomenclature.objects.filter(type=NomType.MATERIAL)
    serializer_class = MaterialCRUDSerializer


class CreateMaterialsView(APIView):
    permission_classes = [IsAuthenticated, IsStaff]

    @extend_schema(request=CreateMaterialsSerializer())
    def post(self, request):
        staff = request.user.staff_profile
        warehouse = staff.warehouses.first()
        data = request.data

        materials_data = []

        for d in data['details']:
            materials_data.append(
                Nomenclature(
                    title=data['title'],
                    type=NomType.MATERIAL,
                    unit=data['unit'],
                    cost_price=d['cost_price'],
                    color_id=d['color'],
                    coefficient=d['coefficient'],
                    status=NomStatus.CUT
                )
            )

        created_materials = Nomenclature.objects.bulk_create(materials_data)
        materials_info = [{'id': op.id, 'price': op.cost_price} for op in created_materials]

        quantity = Quantity.objects.create(in_warehouse=warehouse, status=QuantityStatus.ACTIVE)
        count_data = []
        create_data = []

        for m in materials_info:
            count_data.append(
                NomCount(
                    warehouse=warehouse,
                    nomenclature_id=m['id'],
                    amount=1
                )
            )
            create_data.append(
                QuantityNomenclature(
                    quantity=quantity,
                    nomenclature_id=m['id'],
                    amount=1,
                    price=m['price']
                )
            )
        NomCount.objects.bulk_create(count_data)
        QuantityNomenclature.objects.bulk_create(create_data)

        QuantityHistory.objects.create(quantity=quantity, staff_id=staff.id, staff_name=staff.name,
                                       staff_surname=staff.surname, status=quantity.status)


        return Response('Success!', status=status.HTTP_200_OK)



class StockInputView(APIView):
    permission_classes = [IsAuthenticated, IsStaff]

    @extend_schema(request=StockInputSerializer(many=True))
    def post(self, request):
        staff = request.user.staff_profile
        data = request.data
        warehouse = Warehouse.objects.filter(staffs=staff).first()
        quantity = Quantity.objects.create(in_warehouse=warehouse, status=QuantityStatus.ACTIVE)

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
            nom_count_updates = []
            nomenclature_updates = []

            for item in data:
                nomenclature = Nomenclature.objects.get(id=item['product_id'])
                price = item['price']
                amount = item['amount']

                obj, created = NomCount.objects.get_or_create(
                    warehouse=warehouse,
                    nomenclature=nomenclature
                )

                if created:
                    old_amount = 0
                    old_price = 0
                else:
                    old_amount = obj.amount
                    old_price = nomenclature.cost_price or 0

                obj.amount = old_amount + amount
                nom_count_updates.append(obj)

                total_amount = obj.amount
                total_cost = (old_amount * old_price) + (amount * price)

                if total_amount > 0:
                    nomenclature.cost_price = total_cost / total_amount
                else:
                    nomenclature.cost_price = 0
                nomenclature_updates.append(nomenclature)

            NomCount.objects.bulk_update(nom_count_updates, ['amount'])
            Nomenclature.objects.bulk_update(nomenclature_updates, ['cost_price'])

        return Response('Success!', status=status.HTTP_200_OK)


class StockOutputView(APIView):
    permission_classes = [IsAuthenticated, IsStaff]

    @extend_schema(request=StockOutputSerializer())
    def post(self, request):
        staff = request.user.staff_profile
        warehouse = Warehouse.objects.filter(staffs=staff).first()
        data = request.data

        warehouse_id = data['output_warehouse_id']
        if warehouse_id:
            quantity = Quantity.objects.create(in_warehouse_id=warehouse_id,
                                               out_warehouse=warehouse,
                                               status=QuantityStatus.PROGRESSING)
        else:
            quantity = Quantity.objects.create(out_warehouse=warehouse,
                                               status=data['status'])

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


class MovingListView(ListAPIView):
    permission_classes = [IsAuthenticated, IsStaff]
    serializer_class = MovingListSerializer

    def get_queryset(self):
        manager = self.request.user.staff_profile
        warehouse = manager.warehouses.first()
        if not warehouse:
            raise ValidationError("У менеджера не назначен склад.")

        movements = warehouse.in_quants.select_related('out_warehouse').filter(status=QuantityStatus.PROGRESSING)
        return movements


class MovingDetailView(APIView):
    def get_object(self, pk):
        try:
            return Quantity.objects.prefetch_related('quantities').get(pk=pk)
        except:
            return Response('Quantity does not exist!', status=status.HTTP_404_NOT_FOUND)

    @extend_schema(
        responses=MovingSerializer(),
    )
    def get(self, request, pk):
        quantity = self.get_object(pk)
        serializer = MovingSerializer(quantity)
        return Response(serializer.data)


class StockDefectiveView(APIView):
    permission_classes = [IsAuthenticated, IsStaff]

    @extend_schema(request=StockDefectiveSerializer())
    def post(self, request):
        staff = request.user.staff_profile
        data = request.data
        warehouse = Warehouse.objects.filter(staffs=staff).first()
        quantity = Quantity.objects.create(out_warehouse=warehouse, status=data['status'])

        create_data = []
        for i in data['products']:
            create_data.append(
                QuantityNomenclature(
                    quantity=quantity,
                    nomenclature_id=i['product_id'],
                    amount=i['amount'],
                    comment=i['comment']
                )
            )
        QuantityNomenclature.objects.bulk_create(create_data)

        QuantityHistory.objects.create(quantity=quantity, staff_id=staff.id, staff_name=staff.name,
                                       staff_surname=staff.surname, status=quantity.status)
        warehouse = Warehouse.objects.filter(staffs=staff).first()
        with transaction.atomic():
            for i in data['products']:
                NomCount.objects.filter(
                    warehouse=warehouse,
                    nomenclature_id=i["product_id"]
                ).update(amount=F('amount') - i["amount"])

        return Response({"quantity_id": quantity.id}, status=status.HTTP_200_OK)


class StockDefectiveFileView(APIView):
    permission_classes = [IsAuthenticated, IsStaff]

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
    permission_classes = [IsAuthenticated, IsStaff]

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
                nom_count_updates = []
                nomenclature_updates = []
                for update in updates:
                    nomenclature = update.nomenclature
                    obj, created = NomCount.objects.get_or_create(
                        warehouse=quantity.in_warehouse,
                        nomenclature=nomenclature
                    )

                    if created:
                        old_amount = 0
                        old_price = 0
                    else:
                        old_amount = obj.amount
                        old_price = nomenclature.cost_price or 0

                    obj.amount = old_amount + update.amount
                    nom_count_updates.append(obj)

                    total_amount = obj.amount
                    total_cost = (old_amount * old_price) + (update.amount * update.price)

                    if total_amount > 0:
                        nomenclature.cost_price = total_cost / total_amount
                    else:
                        nomenclature.cost_price = 0
                    nomenclature_updates.append(nomenclature)
                NomCount.objects.bulk_update(nom_count_updates, ['amount'])
                Nomenclature.objects.bulk_update(nomenclature_updates, ['cost_price'])

        return Response('Success!', status=status.HTTP_200_OK)


class WarehouseListView(ListAPIView):
    permission_classes = [IsAuthenticated, IsStaff]
    serializer_class = WarehouseListSerializer

    def get_queryset(self):
        manager = self.request.user.staff_profile
        if manager.role == StaffRole.WAREHOUSE:
            queryset = Warehouse.objects.exclude(id__in=manager.warehouses.values_list('id', flat=True))
        else:
            queryset = Warehouse.objects.all()
        return queryset


class QuantityHistoryListView(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated, IsStaff]
    pagination_class = StandardPagination
    queryset = QuantityHistory.objects.all()

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return QuantityHistoryDetailSerializer
        return QuantityHistoryListSerializer

    def get_queryset(self):
        if self.action == 'retrieve':
            return QuantityHistory.objects.select_related(
                'quantity', 'quantity__in_warehouse', 'quantity__out_warehouse').order_by('-id')
        staff = self.request.user.staff_profile
        warehouse = staff.warehouses.first()
        return QuantityHistory.objects.filter(
                Q(quantity__out_warehouse=warehouse) | Q(quantity__in_warehouse=warehouse)
                ).select_related(
                    'quantity', 'quantity__in_warehouse', 'quantity__out_warehouse'
                ).order_by('-id')







