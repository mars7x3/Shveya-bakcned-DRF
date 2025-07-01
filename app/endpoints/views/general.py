from rest_framework import status, viewsets
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response


from endpoints.permissions import IsStaff, IsDirectorAndTechnologist
from my_db.enums import PartyStatus, OrderStatus
from my_db.models import Rank, Size, Color
from serializers.general import SizeSerializer, RankSerializer, ColorSerializer


class RankListView(ListAPIView):
    permission_classes = [IsAuthenticated, IsStaff]
    queryset = Rank.objects.all()
    serializer_class = RankSerializer


class SizeListView(ListAPIView):
    permission_classes = [IsAuthenticated, IsStaff]
    serializer_class = SizeSerializer
    queryset = Size.objects.all()


class SizeModelViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsStaff]
    queryset = Size.objects.all()
    serializer_class = SizeSerializer

    def destroy(self, request, *args, **kwargs):
        size = self.get_object()
        works = size.work_details.filter(work__payment__isnull=True)
        if works:
            return Response({"text": "У данного цвета есть не оплаченные работы сотрудников!"})

        parties = size.party_details.filter(party__status=PartyStatus.MODERATED)
        if parties:
            return Response({"text": "У данного цвета есть активные наряды!"})

        products = size.amounts.exclude(order_product__order__status=OrderStatus.DONE)
        if products:
            return Response({"text": "У данного цвета есть активные заказы!"})

        self.perform_destroy(size)
        return Response(status=status.HTTP_204_NO_CONTENT)


class RankModelViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsStaff]
    queryset = Rank.objects.all()
    serializer_class = RankSerializer

    def destroy(self, request, *args, **kwargs):
        rank = self.get_object()
        rank.is_active = False
        rank.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ColorModelViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsStaff]
    queryset = Color.objects.all()
    serializer_class = ColorSerializer

