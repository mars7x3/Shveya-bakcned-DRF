import datetime

from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from endpoints.permissions import IsDirectorAndTechnologist
from my_db.models import Plan, Order
from serializers.dashboard import PlanSerializer


class PlanCRUDView(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsDirectorAndTechnologist]
    queryset = Plan.objects.all()
    serializer_class = PlanSerializer


class StatisticView(APIView):
    permission_classes = [IsAuthenticated, IsDirectorAndTechnologist]

    def get(self, request):
        date = request.query_params.get('from_date')
        date = timezone.make_aware(datetime.datetime.strptime(date, "%d-%m-%Y"))

        plan = Plan.objects.filter(date__month=date.month)
        orders = Order.objects.filter(created_at__month=date.month)

        data = {
            "order": {
                "plan": {
                    "income": plan.income_amount, # доход
                    "orders": plan.order_amount  # количество заказов
                },
                "fact": {
                    "income": 0,  # доход
                    "consumption": 0,  # расход
                    "profit": 0,  # прибыль
                    "orders": 0  # количество заказов
                }
            },
            "staff": {
                "avg_performance": 0,  # средняя производительность сотрудника (операции считать нужно)
                "performance": 0,  # сколько операций проделали
                "fine": 0,  # сколько штрафов
                "done": 0,  # сколько заработали
                "time": 0  # время работы
            },
            "product": {
                "produced": 0,  # сколько товаров создано
            },
            "machine": {
                "time": 0,  # сколько по времени работала машина,
                "service": 0  # сколько по деньгам ушло на тех обслуживание
            }
        }
        return Response(data, status=status.HTTP_200_OK)

