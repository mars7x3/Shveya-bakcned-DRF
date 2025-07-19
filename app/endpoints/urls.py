from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .views.calculation import OperationTitleListView, ConsumableTitleListView, OperationDetailView, \
    ConsumableDetailView, CalculationViewSet, CalculationListView, ClientNameListView, ProductTitleList, \
    GETProductInfoView
from .views.dashboard import PlanCRUDView, StatisticView
from .views.nomenclature import GPListView, GPModelViewSet, PatternCRUDView, CombinationModelViewSet, GPDetailView, \
    OperationModelViewSet, EquipmentModelViewSet, MaterialListView, PatternListView, ProductListView, \
    EquipmentImageCRUDView, EquipmentServiceView, FileCRUDView, FileListView, MaterialListMyView
from .views.order import OrderReadView, OrderModelViewSet, InvoiceDataVie, ClientOrdersView
from .views.payment import PaymentCreateView, SalaryInfoView, PaymentHistoryListView, PaymentFilesCreateView, \
    SalaryCreateView, PaymentDetailView, MyPaymentHistoryListView, MyPaymentDetailView
from .views.sample import CombinationFileCRUDVIew, SampleCombinationListView, SampleOperationListView
from .views.user_crud import StaffInfoView, StaffModelViewSet, ClientModelViewSet, ClientListView, ClientFileCRUDView, \
    StaffListView
from .views.general import RankListView, SizeListView, RankModelViewSet, ColorModelViewSet, SizeModelViewSet
from .views.warehouse import WarehouseModelViewSet, WarehouseMaterialListView, MaterialModelViewSet, StockInputView, \
    StockOutputView, StockDefectiveView, StockDefectiveFileView, StockOutputUpdateView, MovingListView, \
    MovingDetailView, MyMaterialListView, WarehouseListView, QuantityHistoryListView, CreateMaterialsView
from .views.work import WorkStaffListView, MyWorkListView, PartyCreateCRUDView, OrderInfoListView, PartyListView, \
    ProductInfoView, PartyInfoListView, ProductOperationListView, WorkCRUDView, WorkReadListView, \
    WorkReadDetailView

router = DefaultRouter()

router.register('user/staff/crud', StaffModelViewSet)
router.register('user/client/crud', ClientModelViewSet)
router.register('general/rank/crud', RankModelViewSet)
router.register('general/color/crud', ColorModelViewSet)
router.register('general/size/crud', SizeModelViewSet)
router.register('product/crud', GPModelViewSet)
router.register('product/combination/crud', CombinationModelViewSet)
router.register('product/operation/crud', OperationModelViewSet)
router.register('equipment/crud', EquipmentModelViewSet)
router.register('order/crud', OrderModelViewSet)
router.register('order/list', OrderReadView)
router.register('client/order/list', ClientOrdersView)
router.register('warehouse/crud', WarehouseModelViewSet)
router.register('warehouse/material/crud', MaterialModelViewSet)
router.register('warehouse/history/list', QuantityHistoryListView)
router.register('work/party/list', PartyListView)
router.register('work/party/crud', PartyCreateCRUDView)
router.register('work/crud', WorkCRUDView)

router.register('dashboard/plan/crud', PlanCRUDView)
router.register('calculation/crud', CalculationViewSet)
router.register('sample/combination-files/crud', CombinationFileCRUDVIew)
router.register('sample/combinations/list', SampleCombinationListView)
router.register('sample/operations/list', SampleOperationListView)

urlpatterns = [
    path('admin/', admin.site.urls),

    path('api/v1/', include([
        path('schema/', SpectacularAPIView.as_view(), name='schema'),
        path('swagger/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
        path('schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

        path('general/ranks/', RankListView.as_view()),
        path('general/sizes/', SizeListView.as_view()),

        path('token/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
        path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

        path('user/staff/info/', StaffInfoView.as_view()),
        path('user/client/files/', ClientFileCRUDView.as_view()),
        path('user/staff/list/', StaffListView.as_view()),

        path('order/clients/list/', ClientListView.as_view()),
        path('order/products/list/', ProductListView.as_view()),
        path('order/invoice/data/', InvoiceDataVie.as_view()),


        path('material/list/', MaterialListView.as_view()),
        path('material/list/my/', MaterialListMyView.as_view()),

        path('product/list/', GPListView.as_view()),
        path('product/detail/<int:pk>/', GPDetailView.as_view()),
        path('product/images/crud', PatternCRUDView.as_view()),
        path('product/files/crud', FileCRUDView.as_view()),
        path('product/<int:pk>/images/', PatternListView.as_view()),
        path('product/<int:pk>/files/', FileListView.as_view()),

        path('warehouse/materials/list/', WarehouseMaterialListView.as_view()),
        path('warehouse/my-materials/list/', MyMaterialListView.as_view()),
        path('warehouse/input/', StockInputView.as_view()),
        path('warehouse/output/', StockOutputView.as_view()),
        path('warehouse/output/update/', StockOutputUpdateView.as_view()),
        path('warehouse/movements/', MovingListView.as_view()),
        path('warehouse/movements/<int:pk>/', MovingDetailView.as_view()),
        path('warehouse/defective/', StockDefectiveView.as_view()),
        path('warehouse/defective/files/', StockDefectiveFileView.as_view()),
        path('warehouse/list/', WarehouseListView.as_view()),
        path('warehouse/materials/create/', CreateMaterialsView.as_view()),


        path('work/staffs/list/', WorkStaffListView.as_view()),
        path('work/history/list/my/', MyWorkListView.as_view()),
        path('work/order-info/list/', OrderInfoListView.as_view()),
        path('work/product-info/', ProductInfoView.as_view()),
        path('work/get-party-info/', PartyInfoListView.as_view()),
        path('work/get-product-operations/', ProductOperationListView.as_view()),
        path('work/get-works/', WorkReadListView.as_view()),
        path('work/get-works/<int:pk>/', WorkReadDetailView.as_view()),


        path('payment/create/', PaymentCreateView.as_view()),
        path('payment/files/create/', PaymentFilesCreateView.as_view()),
        path('payment/salary/create/', SalaryCreateView.as_view()),
        path('payment/salary-info/<int:pk>/', SalaryInfoView.as_view()),
        path('payment/history/list/<int:pk>/', PaymentHistoryListView.as_view()),
        path('payment/history/list/my/', MyPaymentHistoryListView.as_view()),
        path('payment/history/detail/<int:pk>/', PaymentDetailView.as_view()),
        path('payment/history/detail/my/<int:pk>/', MyPaymentDetailView.as_view()),

        path('dashboard/statistic/', StatisticView.as_view()),

        path('equipment/images/', EquipmentImageCRUDView.as_view()),
        path('equipment/services/', EquipmentServiceView.as_view()),

        path('calculation/operations/titles/', OperationTitleListView.as_view()),
        path('calculation/operations/detail/<int:pk>/', OperationDetailView.as_view()),
        path('calculation/consumables/titles/', ConsumableTitleListView.as_view()),
        path('calculation/consumables/detail/<int:pk>/', ConsumableDetailView.as_view()),
        path('calculation/list/', CalculationListView.as_view()),
        path('calculation/clients/names/', ClientNameListView.as_view()),
        path('calculation/get-product-titles/', ProductTitleList.as_view()),
        path('calculation/get-product-info/', GETProductInfoView.as_view()),


        path('', include(router.urls)),
    ])),
]
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)