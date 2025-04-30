# Django core imports
from django import views
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

# Local app imports
from .views import (
    OtherPurchaseCreateView,
    OtherPurchaseDeleteView,
    OtherPurchaseListView,
    PurchaseListView,
    PurchaseDetailView,
    PurchaseCreateView,
    PurchaseReportDeleteView,
    PurchaseReportListView,
    PurchaseReportView,
    PurchaseUpdateView,
    PurchaseDeleteView,
    SaleListView,
    SaleDetailView,
    SaleCreateView,
    SaleDeleteView,
    SalesReportDeleteView,
    SalesReportListView,
    SalesReportView,
    export_report,
    get_raw_materials,      
    BatchListView, BatchCreateView, BatchDeleteView,
    get_operations_inventory,

    export_sales_to_excel,
    export_purchases_to_excel
)

# URL patterns
urlpatterns = [
    # Purchase URLs
    path('purchases/', PurchaseListView.as_view(), name='purchaseslist'),
    path(
         'purchase/<slug:slug>/', PurchaseDetailView.as_view(),
         name='purchase-detail'
     ),
    path('get-raw-materials/', get_raw_materials, name='get_raw_materials'),

    path('new-purchase/', PurchaseCreateView, name='purchase-create'),
    path(
         'purchase/<int:pk>/update/', PurchaseUpdateView.as_view(),
         name='purchase-update'
     ),
    path(
         'purchase/<int:pk>/delete/', PurchaseDeleteView.as_view(),
         name='purchase-delete'
     ),

    # Sale URLs
    path('sales/', SaleListView.as_view(), name='saleslist'),
    path('sale/<int:pk>/', SaleDetailView.as_view(), name='sale-detail'),
    path('new-sale/', SaleCreateView, name='sale-create'),
    path(
         'sale/<slug:slug>/delete/', SaleDeleteView.as_view(),
         name='sale-delete'
     ),
    path('new-purchase/', PurchaseCreateView, name='purchase-create'),

    path('batches/', BatchListView.as_view(), name='batch-list'),
    path('batches/create/', BatchCreateView.as_view(), name='batch-create'),
    path('batches/<int:pk>/delete/', BatchDeleteView.as_view(), name='batch-delete'),

    path('other-purchases/', OtherPurchaseListView.as_view(), name='other-purchases-list'),
    path('other-purchases/create/', OtherPurchaseCreateView.as_view(), name='other-purchase-create'),
    path('other-purchases/<int:pk>/delete/', OtherPurchaseDeleteView.as_view(), name='other-purchase-delete'),
    path('get-operations-inventory/', get_operations_inventory, name='get_operations_inventory'),




    # Sales and purchases export
    path('sales/export/', export_sales_to_excel, name='sales-export'),
    path('purchases/export/', export_purchases_to_excel,
         name='purchases-export'),

    # Sales Reports
    path('reports/sales/', SalesReportView.as_view(), name='create-sales-report'),
    path('reports/sales/list/', SalesReportListView.as_view(), name='sales-reports-list'),
    path('reports/sales/<int:pk>/delete/', SalesReportDeleteView.as_view(), name='delete-sales-report'),
    
    # Purchase Reports
    path('reports/purchases/', PurchaseReportView.as_view(), name='create-purchase-report'),
    path('reports/purchases/list/', PurchaseReportListView.as_view(), name='purchase-reports-list'),
    path('reports/purchases/<int:pk>/delete/', PurchaseReportDeleteView.as_view(), name='delete-purchase-report'),
    
    # Export
    path('reports/export/<str:type>/<int:pk>/', export_report, name='report-export'),
]

# Static media files configuration for development
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
