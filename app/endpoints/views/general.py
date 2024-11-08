from rest_framework import status, viewsets
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response


from endpoints.permissions import IsStaff, IsDirectorAndTechnologist
from my_db.models import Rank, Size, SizeCategory
from serializers.general import SizeSerializer, RankSerializer, SizeCategorySerializer


class RankListView(ListAPIView):
    permission_classes = [IsAuthenticated, IsStaff]
    queryset = Rank.objects.all()
    serializer_class = RankSerializer


class SizeListView(ListAPIView):
    permission_classes = [IsAuthenticated, IsStaff]
    serializer_class = SizeSerializer
    queryset = Size.objects.all()


class SizeCategoryListView(ListAPIView):
    permission_classes = [IsAuthenticated, IsStaff]
    serializer_class = SizeCategorySerializer
    queryset = SizeCategory.objects.prefetch_related('sizes')


class RankModelViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsDirectorAndTechnologist]
    queryset = Rank.objects.all()
    serializer_class = RankSerializer

    def destroy(self, request, *args, **kwargs):
        rank = self.get_object()
        rank.is_active = False
        rank.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class SizeModelViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsDirectorAndTechnologist]
    queryset = Size.objects.all()
    serializer_class = SizeSerializer

    def destroy(self, request, *args, **kwargs):
        size = self.get_object()
        size.is_active = False
        size.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class SizeCategoryModelViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsDirectorAndTechnologist]
    queryset = SizeCategory.objects.prefetch_related('sizes')
    serializer_class = SizeCategorySerializer

    def destroy(self, request, *args, **kwargs):
        size = self.get_object()
        size.is_active = False
        size.save()
        return Response(status=status.HTTP_204_NO_CONTENT)