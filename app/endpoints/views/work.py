from django.db.models import Prefetch, Sum, F, Value, CharField
from django.db.models.functions import Concat
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import status, viewsets, mixins
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet

from endpoints.pagination import StandardPagination
from endpoints.permissions import IsDirectorAndTechnologist, IsStaff, IsCutter, IsAuthor, IsController
from my_db.enums import StaffRole, OrderStatus
from my_db.models import StaffProfile, Work, WorkDetail, Combination, Operation, Nomenclature, Party, Order, \
    OrderProduct
from serializers.work import WorkOutputSerializer, WorkStaffListSerializer, \
    WorkInputSerializer, WorkNomenclatureSerializer, OperationSummarySerializer, MyWorkInputSerializer, \
    WorkModerationListSerializer, WorkModerationSerializer, OrderSerializer, \
    PartyListSerializer, ProductInfoSerializer, \
    PartyGETInfoSerializer, PartyCreateUpdateSerializer, PartyInfoSerializer, \
    WorkCRUDSerializer, \
    GETWorkListSerializer, GETWorkDetailSerializer, RequestSerializer


# class WorkOutputView(APIView):
#     permission_classes = [IsAuthenticated, IsDirectorAndTechnologist]
#
#     @extend_schema(request=WorkOutputSerializer(),
#                    responses={200: {'type': 'object', 'properties': {'text': {'type': 'string'}}}})
#     def post(self, request):
#         data = request.data
#         staffs = StaffProfile.objects.filter(id__in=data['staff_ids'])
#
#         work_detail_create = []
#         for staff in staffs:
#             work = Work.objects.create(staff=staff, order_id=data['order_id'])
#
#             for o in data['operations']:
#                 work_detail_create.append(
#                     WorkDetail(work=work, operation_id=o['operation_id'], amount=o['amount'])
#                 )
#
#         WorkDetail.objects.bulk_create(work_detail_create)
#
#         return Response('Success!', status=status.HTTP_200_OK)


class WorkStaffListView(ListAPIView):
    permission_classes = [IsAuthenticated, IsDirectorAndTechnologist]
    serializer_class = WorkStaffListSerializer
    queryset = StaffProfile.objects.filter(role__in=[StaffRole.SEAMSTRESS, StaffRole.CUTTER])


# class WorkOperationListView(APIView):
#     permission_classes = [IsAuthenticated, IsDirectorAndTechnologist]
#
#     @extend_schema(
#         responses=WorkNomenclatureSerializer(),
#     )
#     def get(self, request, pk):
#         nomenclatures = Nomenclature.objects.filter(
#             products__order_id=pk
#         ).distinct().prefetch_related(
#             Prefetch(
#                 'combinations',
#                 queryset=Combination.objects.prefetch_related(
#                     Prefetch(
#                         'operations',
#                         queryset=Operation.objects.filter(is_active=True).annotate(
#                             required=Sum(F('nomenclature__products__amounts__amount'), default=0),
#                             assigned=Sum('details__amount', default=0),
#                             completed=Sum(
#                                 'details__amount',
#                                 default=0
#                             )
#                         )
#                     )
#                 )
#             )
#         )
#
#         serializer = WorkNomenclatureSerializer(nomenclatures, many=True)
#         return Response(serializer.data)


# class WorkInputView(APIView):
#     permission_classes = [IsAuthenticated, IsDirectorAndTechnologist]
#
#     @extend_schema(request=WorkInputSerializer(),
#                    responses={200: {'type': 'object', 'properties': {'text': {'type': 'string'}}}})
#     def post(self, request):
#         data = request.data
#         staff = StaffProfile.objects.get(id=data['staff_id'])
#
#         work_detail_create = []
#         work = Work.objects.create(staff=staff, order_id=data['order_id'])
#
#         for o in data['operations']:
#             work_detail_create.append(
#                 WorkDetail(work=work, operation_id=o['operation_id'], amount=o['amount'])
#             )
#
#         WorkDetail.objects.bulk_create(work_detail_create)
#
#         return Response('Success!', status=status.HTTP_200_OK)


# class MyWorkInputView(APIView):
#     permission_classes = [IsAuthenticated, IsStaff]
#
#     @extend_schema(request=MyWorkInputSerializer(),
#                    responses={200: {'type': 'object', 'properties': {'text': {'type': 'string'}}}})
#     def post(self, request):
#         data = request.data
#         staff = request.user.staff_profile
#
#         work_detail_create = []
#         work = Work.objects.create(staff=staff, order_id=data['order_id'])
#
#         for o in data['operations']:
#             work_detail_create.append(
#                 WorkDetail(work=work, operation_id=o['operation_id'], amount=o['amount'])
#             )
#
#         WorkDetail.objects.bulk_create(work_detail_create)
#
#         return Response('Success!', status=status.HTTP_200_OK)


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


# class WorkModerationListView(ListAPIView):
#     permission_classes = [IsAuthenticated, IsDirectorAndTechnologist]
#     queryset = Work.objects.all().prefetch_related(
#         Prefetch(
#             'details',
#             queryset=WorkDetail.objects.select_related('operation')
#         )
#     )
#     serializer_class = WorkModerationListSerializer


# class WorkModerationView(APIView):
#     permission_classes = [IsAuthenticated, IsDirectorAndTechnologist]
#
#     @extend_schema(request=WorkModerationSerializer(),
#                    responses={200: {'type': 'object', 'properties': {'text': {'type': 'string'}}}})
#     def post(self, request):
#         data = request.data
#         work = Work.objects.get(id=data['work_id'])
#         work.save()
#
#         return Response('Success!', status=status.HTTP_200_OK)


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
    permission_classes = [IsAuthenticated, IsController]
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
    permission_classes = [IsAuthenticated, IsController]

    def post(self, request):
        product_id = request.data.get('product')

        combinations = Combination.objects.filter(nomenclature=product_id).values('id', 'title')

        return Response(combinations)


class WorkCRUDView(mixins.CreateModelMixin,
                   mixins.UpdateModelMixin,
                   mixins.DestroyModelMixin,
                   GenericViewSet):
    permission_classes = [IsAuthenticated, ]
    queryset = Work.objects.all()
    serializer_class = WorkCRUDSerializer

    def perform_create(self, serializer):
        serializer.save(staff=self.request.user.staff_profile)


class WorkReadDetailView(RetrieveAPIView):
    permission_classes = [IsAuthenticated, IsController]
    queryset = Work.objects.all().select_related('color', 'size', 'staff').prefetch_related('details__combination',
                                                                                                'details__staff')
    pagination_class = StandardPagination
    serializer_class = GETWorkDetailSerializer


class WorkReadListView(APIView):
    permission_classes = [IsAuthenticated, IsController]

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
            party__nomenclature_id=product_id
        ).select_related('color', 'size', 'staff', 'party')

        serializer = GETWorkListSerializer(works, many=True)
        return Response(serializer.data)










