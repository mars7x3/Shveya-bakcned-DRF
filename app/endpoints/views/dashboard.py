import datetime

from django.db.models import Sum, Count, F
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from endpoints.permissions import IsDirectorAndTechnologist
from my_db.enums import PaymentStatus
from my_db.models import Plan, Order, OrderProduct, Work, Payment, EquipmentService, Operation
from serializers.dashboard import PlanSerializer


class PlanCRUDView(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsDirectorAndTechnologist]
    queryset = Plan.objects.all()
    serializer_class = PlanSerializer


class StatisticView(APIView):
    permission_classes = [IsAuthenticated, IsDirectorAndTechnologist]

    def get(self, request):
        date = request.query_params.get('date')
        date = timezone.make_aware(datetime.datetime.strptime(date, "%d-%m-%Y")).month

        plan = Plan.objects.filter(date__month=date).first()

        order_products = OrderProduct.objects.filter(
            order__created_at__month=date
        ).select_related('nomenclature', 'order')

        aggregation = order_products.aggregate(
            income=Sum('price'),
            consumption=Sum(F('nomenclature__cost_price')),
            orders=Count('order_id', distinct=True),
            produced=Sum('amounts__amount')  # Количество произведённых товаров
        )
        income = aggregation.get('income') or 0
        consumption = aggregation.get('consumption') or 0
        profit = income - consumption

        work_qs = Work.objects.filter(
            created_at__month=date
        ).prefetch_related('details__operation').select_related('payment', 'staff')

        operations_aggregation = work_qs.aggregate(
            performance=Sum('details__amount'),
            time=Sum(F('details__amount') * F('details__operation__time')),
        )

        payments_qs = Payment.objects.filter(
            staff__in=work_qs.values('staff'),
            created_at__month=date
        ).select_related('staff')

        payments_aggregation = payments_qs.aggregate(
            fine=Sum('amount', filter=F('status') in [
                PaymentStatus.FINE, PaymentStatus.FINE_CHECKED
            ]),  # Общая сумма штрафов
            done=Sum('amount', filter=F('status') in [
                PaymentStatus.SALARY,
                PaymentStatus.ADVANCE,
                PaymentStatus.ADVANCE_CHECKED,
            ]),  # Общая сумма заработка
        )

        staff_count = work_qs.values('staff').distinct().count()
        avg_performance = operations_aggregation['performance'] / staff_count if staff_count > 0 else 0

        equipment_services_qs = EquipmentService.objects.filter(
            created_at__month=date
        ).select_related('equipment')

        operations_qs = Operation.objects.filter(
            equipment__services__created_at__month=date
        ).select_related('equipment')

        # Агрегация данных
        equipment_service_aggregation = equipment_services_qs.aggregate(
            service_cost=Sum('price')  # Суммарные расходы на обслуживание
        )
        operation_time_aggregation = operations_qs.aggregate(
            total_time=Sum('time')  # Общее время работы оборудования
        )


        data = {
            "order": {
                "plan": {
                    "income": plan.income_amount if plan else 0, # доход
                    "orders": plan.order_amount if plan else 0  # количество заказов
                },
                "fact": {
                    "income": income,  # доход
                    "consumption": consumption,  # расход
                    "profit": profit,  # прибыль
                    "orders": aggregation.get('orders') or 0  # количество заказов
                }
            },
            "staff": {
                "avg_performance": avg_performance or 0,  # Средняя производительность
                "performance": operations_aggregation['performance'] or 0,  # Количество операций
                "fine": payments_aggregation['fine'] or 0,  # Сумма штрафов
                "done": payments_aggregation['done'] or 0,  # Сумма заработка
                "time": operations_aggregation['time'] or 0,  # Общее время работы
            },
            "product": {
                "produced": aggregation.get('produced') or 0,  # сколько товаров создано
            },
            "machine": {
                "time": operation_time_aggregation['total_time'] or 0,  # сколько по времени работала машина,
                "service": equipment_service_aggregation['service_cost'] or 0  # сколько по деньгам ушло на тех обслуживание
            }
        }
        return Response(data, status=status.HTTP_200_OK)

