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


class SizeCategoryModelViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsDirectorAndTechnologist]
    queryset = SizeCategory.objects.prefetch_related('sizes')
    serializer_class = SizeCategorySerializer

    def create(self, request, *args, **kwargs):
        sizes_data = request.data.get('sizes_add', [])
        sizes_delete_data = request.data.get('sizes_delete', [])

        size_category = SizeCategory.objects.create(
            title=request.data.get('title'),
            is_active=request.data.get('is_active', True)
        )

        if sizes_data:
            create_data = [Size(category=size_category, title=size['title']) for size in sizes_data]
            sizes = Size.objects.bulk_create(create_data)
            size_category.sizes.add(*sizes)

        if sizes_delete_data:
            Size.objects.filter(id__in=sizes_delete_data).delete()

        serializer = self.get_serializer(size_category)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        size_category = self.get_object()
        sizes_data = request.data.get('sizes_add', [])
        sizes_delete_data = request.data.get('sizes_delete', [])

        size_category.title = request.data.get('title', size_category.title)
        size_category.is_active = request.data.get('is_active', size_category.is_active)
        size_category.save()

        if sizes_data:
            create_data = [Size(category=size_category, title=size['title']) for size in sizes_data]
            sizes = Size.objects.bulk_create(create_data)
            size_category.sizes.add(*sizes)

        if sizes_delete_data:
            Size.objects.filter(id__in=sizes_delete_data).delete()

        serializer = self.get_serializer(size_category)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        size = self.get_object()
        size.is_active = False
        size.save()
        return Response(status=status.HTTP_204_NO_CONTENT)