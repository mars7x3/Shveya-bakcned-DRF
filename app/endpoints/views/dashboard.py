from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from endpoints.permissions import IsDirectorAndTechnologist
from my_db.models import Plan
from serializers.dashboard import PlanSerializer


class PlanCRUDView(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsDirectorAndTechnologist]
    queryset = Plan.objects.all()
    serializer_class = PlanSerializer


class StatisticView(APIView):
    permission_classes = [IsAuthenticated, IsDirectorAndTechnologist]

    def get(self, request):
        data = {
            "order": {
                "plan": {
                    "income": 0,
                    "orders": 0
                },
                "fact": {
                    "income": 0,
                    "consumption": 0,
                    "profit": 0,
                    "orders": 0
                }
            },
            "staff": {
                "avg_performance": 0,
                "fine": 0,
                "done": 0,
                "machine": 0

            },
            "product": {
                "produced": 0,
                "popular": 0
            }
        }
        return Response(data, status=status.HTTP_200_OK)

