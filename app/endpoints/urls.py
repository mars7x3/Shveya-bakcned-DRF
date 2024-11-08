from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView


from .views.nomenclature import GPListView, GPModelViewSet, PatternCRUDView, CombinationModelViewSet, GPDetailView, \
    OperationModelViewSet, EquipmentModelViewSet
from .views.order import OrderListView
from .views.user_crud import StaffInfoView, StaffModelViewSet, ClientModelViewSet
from .views.general import RankListView, SizeListView, SizeModelViewSet, RankModelViewSet, SizeCategoryListView, \
    SizeCategoryModelViewSet

router = DefaultRouter()

router.register('user/staff/crud', StaffModelViewSet)
router.register('user/client/crud', ClientModelViewSet)
router.register('general/rank/crud', RankModelViewSet)
router.register('general/size/crud', SizeModelViewSet)
router.register('general/size/category/crud', SizeCategoryModelViewSet)
router.register('product/crud', GPModelViewSet)
router.register('product/combination/crud', CombinationModelViewSet)
router.register('product/operation/crud', OperationModelViewSet)
router.register('equipment/crud', EquipmentModelViewSet)





urlpatterns = [
    path('admin/', admin.site.urls),

    path('api/v1/', include([
        path('schema/', SpectacularAPIView.as_view(), name='schema'),
        path('swagger/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
        path('schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

        path('general/ranks/', RankListView.as_view()),
        path('general/sizes/', SizeListView.as_view()),
        path('general/size/categories/', SizeCategoryListView.as_view()),

        path('token/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
        path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

        path('user/staff/info/', StaffInfoView.as_view()),

        path('order/list/', OrderListView.as_view()),

        path('product/list/', GPListView.as_view()),
        path('product/crud/<int:pk>/', GPDetailView.as_view()),
        path('product/images/crud', PatternCRUDView.as_view()),


        path('', include(router.urls)),
    ])),
]
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)