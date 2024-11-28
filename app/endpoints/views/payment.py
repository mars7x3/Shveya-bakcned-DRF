from django.db.models import Sum
from drf_spectacular.utils import extend_schema
from rest_framework import status

from rest_framework.generics import CreateAPIView, ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from endpoints.permissions import IsDirectorAndTechnologist
from my_db.enums import WorkStatus, PaymentStatus
from my_db.models import Payment, StaffProfile, WorkDetail, PaymentFile
from serializers.payments import WorkPaymentSerializer, SalaryInfoSerializer, WorkPaymentFileCRUDSerializer


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
            .annotate(total_amount=Sum("amount"))
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

        serializer = WorkPaymentSerializer(works)
        return Response(serializer.data)