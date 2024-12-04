from django.db.models import Prefetch, Sum, F, Q, IntegerField, Value, Case, When
from drf_spectacular.utils import extend_schema
from rest_framework import status, viewsets, mixins
from rest_framework.generics import ListAPIView, CreateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet

from endpoints.permissions import IsDirectorAndTechnologist, IsStaff
from my_db.enums import WorkStatus, StaffRole
from my_db.models import StaffProfile, Work, WorkDetail, Combination, Operation, Payment, Nomenclature
from serializers.work import WorkOutputSerializer, WorkStaffListSerializer, WorkCombinationSerializer, \
    WorkInputSerializer, WorkNomenclatureSerializer


class WorkOutputView(APIView):
    permission_classes = [IsAuthenticated, IsDirectorAndTechnologist]

    @extend_schema(request=WorkOutputSerializer())
    def post(self, request):
        data = request.data
        staffs = StaffProfile.objects.filter(id__in=data['staff_ids'])

        work_detail_create = []
        for staff in staffs:
            work = Work.objects.create(staff=staff, order_id=data['order_id'], status=WorkStatus.NEW)

            for o in data['operations']:
                work_detail_create.append(
                    WorkDetail(work=work, operation_id=o['operation_id'], amount=o['amount'])
                )

        WorkDetail.objects.bulk_create(work_detail_create)

        return Response('Success!', status=status.HTTP_200_OK)


class WorkStaffListView(ListAPIView):
    permission_classes = [IsAuthenticated, IsDirectorAndTechnologist]
    serializer_class = WorkStaffListSerializer
    queryset = StaffProfile.objects.filter(role__in=[StaffRole.SEAMSTRESS, StaffRole.CUTTER])


class WorkOperationListView(APIView):
    permission_classes = [IsAuthenticated, IsDirectorAndTechnologist]

    @extend_schema(
        responses=WorkNomenclatureSerializer(),
    )
    def get(self, request, pk):
        nomenclatures = Nomenclature.objects.filter(
            products__order_id=pk
        ).distinct().prefetch_related(
            Prefetch(
                'combinations',
                queryset=Combination.objects.prefetch_related(
                    Prefetch(
                        'operations',
                        queryset=Operation.objects.filter(is_active=True).annotate(
                            required=Sum(F('nomenclature__products__amounts__amount'), default=0),
                            assigned=Sum('details__amount', default=0),
                            completed=Sum(
                                'details__amount',
                                filter=Q(details__work__status=WorkStatus.DONE),
                                default=0
                            )
                        )
                    )
                )
            )
        )

        serializer = WorkNomenclatureSerializer(nomenclatures, many=True)
        return Response(serializer.data)


class WorkInputView(APIView):
    permission_classes = [IsAuthenticated, IsDirectorAndTechnologist]

    @extend_schema(request=WorkInputSerializer())
    def post(self, request):
        data = request.data
        staff = StaffProfile.objects.get(id=data['staff_id'])

        work_detail_create = []
        work = Work.objects.create(staff=staff, order_id=data['order_id'], status=WorkStatus.DONE)

        for o in data['operations']:
            work_detail_create.append(
                WorkDetail(work=work, operation_id=o['operation_id'], amount=o['amount'])
            )

        WorkDetail.objects.bulk_create(work_detail_create)

        return Response('Success!', status=status.HTTP_200_OK)


class MyWorkListView(APIView):
    permission_classes = [IsAuthenticated, IsStaff]

    @extend_schema(request=WorkInputSerializer())
    def get(self, request):
        staff = request.user.staff_profile

        operations = (
            WorkDetail.objects.filter(
                work__staff=staff
            )
            .values(
                "operation_id",
                "operation__title",
                "work__order_id"
            )
            .annotate(
                need_amount=Sum(
                    Case(
                        When(work__status=WorkStatus.NEW, then=F("amount")),
                        default=Value(0),
                        output_field=IntegerField()
                    )
                ),
                done_amount=Sum(
                    Case(
                        When(work__status=WorkStatus.DONE, then=F("amount")),
                        default=Value(0),
                        output_field=IntegerField()
                    )
                ),
                moderation_amount=Sum(
                    Case(
                        When(work__status=WorkStatus.MODERATION, then=F("amount")),
                        default=Value(0),
                        output_field=IntegerField()
                    )
                )
            )
            .order_by("-work__order_id")
        )


        operation_mapping = {}

        for item in operations:
            key = (item["operation_id"], item["operation__title"])  # Ключ для группировки
            if key not in operation_mapping:
                operation_mapping[key] = {
                    "operation_id": item["operation_id"],
                    "operation_title": item["operation__title"],
                    "order_id": item["work__order_id"],
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
