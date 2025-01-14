from rest_framework import status, viewsets
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response


from endpoints.permissions import IsStaff, IsDirectorAndTechnologist
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


class RankModelViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsDirectorAndTechnologist]
    queryset = Rank.objects.all()
    serializer_class = RankSerializer

    def destroy(self, request, *args, **kwargs):
        rank = self.get_object()
        rank.is_active = False
        rank.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

