from django.db.models import Sum, F
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.exceptions import NotFound

from rest_framework.generics import CreateAPIView, ListAPIView, RetrieveAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from endpoints.permissions import IsDirectorAndTechnologist
from my_db.enums import WorkStatus, PaymentStatus
from my_db.models import Payment, StaffProfile, WorkDetail, PaymentFile, Work
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
        works = (
            WorkDetail.objects.filter(
                work__staff_id=pk,
                work__status=WorkStatus.DONE,
                work__payment__isnull=True,
            )
            .values("operation")
            .annotate(total_amount=Sum("amount"), price=F('operation__price'))
        )
        payments = Payment.objects.filter(
            staff_id=pk,
            status__in=[PaymentStatus.FINE, PaymentStatus.ADVANCE]
        )
        data = {
            "works": works,
            "payments": payments,
        }
        serializer = SalaryInfoSerializer(data)
        return Response(serializer.data)


class PaymentHistoryListView(APIView):
    permission_classes = [IsAuthenticated, IsDirectorAndTechnologist]

    @extend_schema(
        responses=WorkPaymentSerializer(),
    )
    def get(self, request, pk):
        works = Payment.objects.filter(staff_id=pk)

        serializer = WorkPaymentSerializer(works, many=True)
        return Response(serializer.data)


class SalaryCreateView(APIView):
    permission_classes = [IsAuthenticated, IsDirectorAndTechnologist]

    @extend_schema(
        request=SalaryCreateSerializer(),
        responses={200: {'type': 'object', 'properties': {'text': {'type': 'string'}}}}
    )
    def post(self, request):
        serializer = SalaryCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        staff_id = serializer.validated_data.get('staff_id')
        payment = Payment.objects.create(
            staff_id=staff_id,
            status=PaymentStatus.SALARY,
            amount=serializer.validated_data.get('amount')
        )

        Work.objects.filter(
            staff_id=staff_id,
            status=WorkStatus.DONE,
            payment__isnull=True
        ).update(payment=payment)

        return Response('Success!', status=status.HTTP_200_OK)



class PaymentDetailView(RetrieveAPIView):
    permission_classes = [IsAuthenticated, IsDirectorAndTechnologist]
    queryset = Payment.objects.all()
    serializer_class = WorkPaymentDetailSerializer
