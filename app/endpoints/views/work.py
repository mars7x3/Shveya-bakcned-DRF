from django.db.models import F, Value, CharField
from django.db.models.functions import Concat
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import status, viewsets, mixins
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet

from endpoints.pagination import StandardPagination
from endpoints.permissions import IsStaff, IsCutter
from my_db.enums import StaffRole, OrderStatus, CombinationStatus
from my_db.models import StaffProfile, Work, WorkDetail, Combination,  Party, Order, \
    OrderProduct
from serializers.work import  WorkStaffListSerializer, \
    OperationSummarySerializer, OrderSerializer, \
    PartyListSerializer, ProductInfoSerializer, \
    PartyGETInfoSerializer, PartyCreateUpdateSerializer, PartyInfoSerializer, \
    WorkCRUDSerializer, \
    GETWorkListSerializer, GETWorkDetailSerializer, RequestSerializer


class WorkStaffListView(ListAPIView):
    permission_classes = [IsAuthenticated, IsStaff]
    serializer_class = WorkStaffListSerializer
    queryset = StaffProfile.objects.filter(role__in=[StaffRole.SEAMSTRESS, StaffRole.CUTTER])


class MyWorkListView(APIView):
    permission_classes = [IsAuthenticated, IsStaff]

    @extend_schema(request=OperationSummarySerializer(),
                   responses={200: {'type': 'object', 'properties': {'text': {'type': 'string'}}}})
    def get(self, request):
        staff = request.user.staff_profile

        operations = (
            WorkDetail.objects.filter(
                work__staff=staff
            )
            .values(
                "operation_id",
                "operation__title",
                "work__order_id",
                "work__order__client__name",
                "work__order__client__surname"
            )
            .annotate(
                order_client=Concat(
                    F("work__order__client__surname"),
                    Value(" "),
                    F("work__order__client__name"),
                    output_field=CharField()
                ),
            )
            .order_by("-work__order_id")
        )


        operation_mapping = {}

        for item in operations:
            key = (item["operation_id"], item["operation__title"])
            if key not in operation_mapping:
                operation_mapping[key] = {
                    "operation_id": item["operation_id"],
                    "operation_title": item["operation__title"],
                    "order_id": item["work__order_id"],
                    "order_client": item.get("order_client", "N/A"),
                    "need_amount": item["need_amount"] or 0,
                    "done_amount": item["done_amount"] or 0,
                    "moderation_amount": item["moderation_amount"] or 0,
                }
            else:
                operation_mapping[key]["need_amount"] += item["need_amount"] or 0
                operation_mapping[key]["done_amount"] += item["done_amount"] or 0
                operation_mapping[key]["moderation_amount"] += item["moderation_amount"] or 0

        result = list(operation_mapping.values())

        return Response(result)


class OrderInfoListView(ListAPIView):
    permission_classes = [IsAuthenticated, IsStaff]
    queryset = Order.objects.filter(status=OrderStatus.PROGRESS).prefetch_related('products__nomenclature')
    serializer_class = OrderSerializer


class PartyCreateCRUDView(mixins.CreateModelMixin,
                   mixins.UpdateModelMixin,
                   GenericViewSet):
    permission_classes = [IsAuthenticated, IsCutter]
    queryset = Party.objects.all()
    serializer_class = PartyCreateUpdateSerializer

    def perform_create(self, serializer):
        serializer.save(staff=self.request.user.staff_profile)


class PartyListView(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated, IsStaff]
    queryset = Party.objects.all()
    pagination_class = StandardPagination

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return PartyGETInfoSerializer
        return PartyListSerializer

    def get_queryset(self):
        staff = self.request.user.staff_profile
        if staff.role == StaffRole.CUTTER:
            return staff.parties.all()
        return Party.objects.all()


class ProductInfoView(APIView):
    permission_classes = [IsAuthenticated, IsCutter]

    def post(self, request):
        order_id = request.data.get('order')
        product_id = request.data.get('product')

        product = (OrderProduct.objects.filter(
            nomenclature_id=product_id, order_id=order_id
        ).select_related('nomenclature')
                   .prefetch_related('amounts__size', 'amounts__color').first())

        serializer = ProductInfoSerializer(product, context=self.get_renderer_context())
        return Response(serializer.data)


class PartyInfoListView(APIView):
    permission_classes = [IsAuthenticated, IsStaff]
    @extend_schema(request=RequestSerializer(),
                   responses=PartyInfoSerializer(many=True))
    def post(self, request):
        order_id = request.data.get('order')
        product_id = request.data.get('product')

        parties = Party.objects.filter(order_id=order_id, nomenclature_id=product_id).prefetch_related('details__color',
                                                                                                       'details__size')
        serializer = PartyInfoSerializer(parties, many=True, context=self.get_renderer_context())
        return Response(serializer.data)


class ProductOperationListView(APIView):
    permission_classes = [IsAuthenticated, IsStaff]

    def post(self, request):
        product_id = request.data.get('product')
        staff = request.user.staff_profile
        if staff.role == StaffRole.OTK:
            combinations = Combination.objects.filter(
                nomenclature=product_id,
                status__in=[CombinationStatus.OTK, CombinationStatus.DONE]
            ).values('id', 'title')
        else:
            combinations = Combination.objects.filter(
                nomenclature=product_id,
                status=CombinationStatus.ZERO
            ).values('id', 'title')

        return Response(combinations)


class WorkCRUDView(mixins.CreateModelMixin,
                   mixins.UpdateModelMixin,
                   mixins.DestroyModelMixin,
                   GenericViewSet):
    permission_classes = [IsAuthenticated, IsStaff]
    queryset = Work.objects.all()
    serializer_class = WorkCRUDSerializer

    def perform_create(self, serializer):
        serializer.save(staff=self.request.user.staff_profile)


class WorkReadDetailView(RetrieveAPIView):
    permission_classes = [IsAuthenticated, IsStaff]
    queryset = Work.objects.all().select_related('color', 'size', 'staff').prefetch_related(
        'details__staff',
    )
    pagination_class = StandardPagination
    serializer_class = GETWorkDetailSerializer


class WorkReadListView(APIView):
    permission_classes = [IsAuthenticated, IsStaff]

    @extend_schema(
        parameters=[
            OpenApiParameter(name="order", description="ID заказа", required=True, type=int),
            OpenApiParameter(name="product", description="ID продукта", required=True, type=int),
        ],
        responses=GETWorkListSerializer(many=True)
    )
    def get(self, request):
        order_id = request.query_params.get('order')
        product_id = request.query_params.get('product')

        if not order_id or not product_id:
            return Response({"error": "order и product обязательны"}, status=400)

        works = Work.objects.filter(
            party__order_id=order_id,
            party__nomenclature_id=product_id,
        ).select_related('color', 'size', 'staff', 'party')

        serializer = GETWorkListSerializer(works, many=True)
        return Response(serializer.data)


