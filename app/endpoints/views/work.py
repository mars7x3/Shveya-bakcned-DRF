from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from endpoints.permissions import IsDirectorAndTechnologist
from my_db.enums import WorkStatus
from my_db.models import StaffProfile, Work, WorkDetail
from serializers.work import WorkOutputSerializer


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