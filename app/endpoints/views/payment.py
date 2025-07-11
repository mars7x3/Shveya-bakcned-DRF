import datetime

from django.db.models import Sum, DecimalField, Subquery, OuterRef
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import status

from rest_framework.generics import CreateAPIView, RetrieveAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from endpoints.pagination import StandardPagination
from endpoints.permissions import IsDirectorAndTechnologist, IsStaff, IsOwner
from my_db.enums import PaymentStatus, WorkStatus
from my_db.models import Payment, WorkDetail, PaymentFile, Combination
from serializers.payments import WorkPaymentSerializer, SalaryInfoSerializer, WorkPaymentFileCRUDSerializer, \
    SalaryCreateSerializer, WorkPaymentDetailSerializer


class PaymentCreateView(CreateAPIView):
    permission_classes = [IsAuthenticated, IsDirectorAndTechnologist]
    serializer_class = WorkPaymentSerializer
    queryset = Payment.objects.all()


class PaymentFilesCreateView(APIView):
    permission_classes = [IsAuthenticated, IsDirectorAndTechnologist]

    @extend_schema(
        request=WorkPaymentFileCRUDSerializer,
        responses={200: {'type': 'object', 'properties': {'text': {'type': 'string'}}}}
    )
    def post(self, request):
        serializer = WorkPaymentFileCRUDSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        files = request.FILES.getlist('files')
        payment_id = serializer.validated_data.get('payment_id')

        create_data = [PaymentFile(payment_id=payment_id, file=file) for file in files]
        PaymentFile.objects.bulk_create(create_data)

        return Response({"text": "Success!"}, status=status.HTTP_200_OK)


class SalaryInfoView(APIView):
    permission_classes = [IsAuthenticated, IsDirectorAndTechnologist]

    @extend_schema(
        responses=SalaryInfoSerializer(),
    )
    def get(self, request, pk):
        operation_price_subquery = Combination.objects.filter(
            id=OuterRef('combination_id')
        ).annotate(
            total_price=Sum('operations__price')
        ).values('total_price')[:1]

        works_queryset = (
            WorkDetail.objects.filter(
                staff_id=pk,
                status=WorkStatus.NEW,
            )
            .values(
                'combination_id',
                'combination__title',
                'work__party__number',
                'work__party__order_id',
            )
            .annotate(
                total_amount=Sum('amount'),
                price=Subquery(operation_price_subquery, output_field=DecimalField()),
            )
        )

        works = [
            {
                "operation": {
                    "id": work["combination_id"],
                    "title": work["combination__title"],
                    "price": work["price"],
                },
                "total_amount": work["total_amount"],
                "party_number": work["work__party__number"],
                "order_id": work["work__party__order_id"],
            }
            for work in works_queryset
        ]

        payments = Payment.objects.filter(
            staff_id=pk,
            status__in=[PaymentStatus.FINE, PaymentStatus.ADVANCE, PaymentStatus.BONUS]
        )

        work_detail = WorkDetail.objects.filter(
            staff_id=pk,
            status=WorkStatus.NEW
        ).order_by('-created_at').first()

        earliest_created_at = work_detail.created_at.date() if work_detail else None

        data = {
            "works": works,
            "payments": payments,
            "earliest_created_at": earliest_created_at
        }
        serializer = SalaryInfoSerializer(data)
        return Response(serializer.data)


class PaymentHistoryListView(APIView):
    permission_classes = [IsAuthenticated, IsDirectorAndTechnologist]
    pagination_class = StandardPagination

    @extend_schema(
        responses=WorkPaymentSerializer(),
    )
    def get(self, request, pk):
        from_date = request.query_params.get('from_date')
        from_date = timezone.make_aware(datetime.datetime.strptime(from_date, "%d-%m-%Y"))
        to_date = request.query_params.get('to_date')
        to_date = timezone.make_aware(datetime.datetime.strptime(to_date, "%d-%m-%Y"))

        payments = Payment.objects.filter(staff_id=pk, created_at__gte=from_date, created_at__lte=to_date)

        paginator = StandardPagination()
        paginated_payments = paginator.paginate_queryset(payments, request)

        serializer = WorkPaymentSerializer(paginated_payments, many=True)
        return paginator.get_paginated_response(serializer.data)


class SalaryCreateView(APIView):
    permission_classes = [IsAuthenticated, IsDirectorAndTechnologist]

    @extend_schema(
        request=SalaryCreateSerializer(),
        responses={200: {'type': 'object', 'properties': {'text': {'type': 'string'}}}}
    )
    def post(self, request):
        serializer = SalaryCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        staff = serializer.validated_data.get('staff_id')
        payment = Payment.objects.create(
            staff=staff,
            status=PaymentStatus.SALARY,
            amount=serializer.validated_data.get('amount'),
            date_from=serializer.validated_data.get('date_from'),
            date_until=serializer.validated_data.get('date_from'),
        )

        WorkDetail.objects.filter(
            staff=staff,
            status=WorkStatus.NEW,
        ).update(status=WorkStatus.PAID, payment=payment)

        payments = Payment.objects.filter(
            staff=staff,
            status__in=[PaymentStatus.FINE, PaymentStatus.ADVANCE]
        )

        if payments:
            update_data = []
            for p in payments:
                if p.status == PaymentStatus.ADVANCE:
                    p.status = PaymentStatus.ADVANCE_CHECKED
                elif p.status == PaymentStatus.FINE:
                    p.status = PaymentStatus.FINE_CHECKED
                update_data.append(p)

            Payment.objects.bulk_update(update_data, ['status'])

        return Response('Success!', status=status.HTTP_200_OK)



class PaymentDetailView(RetrieveAPIView):
    permission_classes = [IsAuthenticated, ]
    queryset = Payment.objects.all()
    serializer_class = WorkPaymentDetailSerializer


class MyPaymentHistoryListView(APIView):
    permission_classes = [IsAuthenticated, IsStaff]
    pagination_class = StandardPagination

    @extend_schema(
        responses=WorkPaymentSerializer(),
    )
    def get(self, request):
        staff = request.user.staff_profile
        from_date = request.query_params.get('from_date')
        from_date = timezone.make_aware(datetime.datetime.strptime(from_date, "%d-%m-%Y"))
        to_date = request.query_params.get('to_date')
        to_date = timezone.make_aware(datetime.datetime.strptime(to_date, "%d-%m-%Y"))

        payments = Payment.objects.filter(staff=staff, created_at__gte=from_date, created_at__lte=to_date)

        paginator = StandardPagination()
        paginated_payments = paginator.paginate_queryset(payments, request)

        serializer = WorkPaymentSerializer(paginated_payments, many=True)
        return paginator.get_paginated_response(serializer.data)


class MyPaymentDetailView(RetrieveAPIView):
    permission_classes = [IsAuthenticated, IsOwner]
    queryset = Payment.objects.all()
    serializer_class = WorkPaymentDetailSerializer