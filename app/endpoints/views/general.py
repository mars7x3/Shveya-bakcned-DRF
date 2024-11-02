from rest_framework import status
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from endpoints.permissions import IsStaff
from my_db.models import Rank, Size
from serializers.general import SizeSerializer, RankSerializer


class RankListView(ListAPIView):
    permission_classes = [IsAuthenticated, IsStaff]
    queryset = Rank.objects.all()
    serializer_class = RankSerializer


class SizeListView(ListAPIView):
    permission_classes = [IsAuthenticated, IsStaff]
    serializer_class = SizeSerializer
    queryset = Size.objects.all()

