# Django core imports
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

# Local app imports
from . import views
from .views import (
    ProductListView,
    ProductDetailView,
    ProductCreateView,
    ProductUpdateView,
    ProductDeleteView,
    product_qr_code,
    ItemSearchListView,
    DeliveryListView,
    DeliveryDetailView,
    DeliveryCreateView,
    DeliveryUpdateView,
    DeliveryDeleteView,
    get_items_ajax_view,
    CategoryListView,
    CategoryDetailView,
    CategoryCreateView,
    CategoryUpdateView,
    CategoryDeleteView,
    notifications,
    RawMaterialListView,
    RawMaterialCreateView,
    RawMaterialUpdateView,
    RawMaterialDeleteView,
    RawMaterialDetailView,
    RawMaterialSearchView
)

# URL patterns
urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    path('notifications/', notifications, name='notifications'),

    # Product URLs
    path(
        'products/',    
        ProductListView.as_view(),
        name='productslist'
    ),
    path(
        'product/<slug:slug>/',
        ProductDetailView.as_view(),
        name='product-detail'
    ),
    path(
        'new-product/',
        ProductCreateView.as_view(),
        name='product-create'
    ),
    path(
        'product/<slug:slug>/update/',
        ProductUpdateView.as_view(),
        name='product-update'
    ),
    path(
        'product/<slug:slug>/delete/',
        ProductDeleteView.as_view(),
        name='product-delete'
    ),

    # Item search
    path(
        'search/',
        ItemSearchListView.as_view(),
        name='item_search_list_view'
    ),

    # Delivery URLs
    path(
        'deliveries/',
        DeliveryListView.as_view(),
        name='deliveries'
    ),
    path(
        'delivery/<slug:slug>/',
        DeliveryDetailView.as_view(),
        name='delivery-detail'
    ),
    path(
        'new-delivery/',
        DeliveryCreateView.as_view(),
        name='delivery-create'
    ),
    path(
        'delivery/<int:pk>/update/',
        DeliveryUpdateView.as_view(),
        name='delivery-update'
    ),
    path(
        'delivery/<int:pk>/delete/',
        DeliveryDeleteView.as_view(),
        name='delivery-delete'
    ),

    # AJAX view
    path(
        'get-items/',
        get_items_ajax_view,
        name='get_items'
    ),

    # Category URLs
    path(
        'categories/',
        CategoryListView.as_view(),
        name='category-list'
    ),
    path(
        'categories/<int:pk>/',
        CategoryDetailView.as_view(),
        name='category-detail'
    ),
    path(
        'categories/create/',
        CategoryCreateView.as_view(),
        name='category-create'
    ),
    path(
        'categories/<int:pk>/update/',
        CategoryUpdateView.as_view(),
        name='category-update'
    ),
    path(
        'categories/<int:pk>/delete/',
        CategoryDeleteView.as_view(),
        name='category-delete'
    ),
    path('qr-code/<slug:slug>/', product_qr_code, name='product-qr-code'),

    #Raw Materials URL
    path('raw-materials/', RawMaterialListView.as_view(), name='raw-material-list'),
    path('raw-material/create/', RawMaterialCreateView.as_view(), name='raw-material-create'),
    path('raw-material/<int:pk>/', RawMaterialDetailView.as_view(), name='raw-material-detail'),
    path('raw-material/<int:pk>/update/', RawMaterialUpdateView.as_view(), name='raw-material-update'),
    path('raw-material/<int:pk>/delete/', RawMaterialDeleteView.as_view(), name='raw-material-delete'),
    path('raw-materials/', RawMaterialSearchView.as_view(), name='raw-material-list'),
    
    path('operations-inventory/', views.OperationsInventoryListView.as_view(), name='operations-inventory-list'),
    path('operations-inventory/create/', views.OperationsInventoryCreateView.as_view(), name='operations-inventory-create'),
    path('operations-inventory/<int:pk>/update/', views.OperationsInventoryUpdateView.as_view(), name='operations-inventory-update'),
    path('operations-inventory/<int:pk>/delete/', views.OperationsInventoryDeleteView.as_view(), name='operations-inventory-delete'),

     path('recipes/create/', views.recipe_create, name='recipe_create'),
    path('recipes/', views.recipe_list, name='recipe_list'),
    path('recipes/delete/<int:pk>/', views.recipe_delete, name='recipe_delete'),
    path('recipe-generator/', views.recipe_generator, name='recipe_generator'),
     path('recipes/add-ingredients/<int:recipe_id>/', views.add_ingredients, name='add_ingredients'),
    path('delete-ingredient/<int:pk>/', views.delete_ingredient, name='delete_ingredient'),


    
]

# Static media files configuration for development
if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )
