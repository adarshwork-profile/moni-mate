from django.urls import path
from . import views

app_name = 'assets'

urlpatterns = [
    path('',views.balance_sheet,name='wealth'),
    path('add-assets/',views.add_asset,name='add-assets'),
    path('asset-view/<int:asset_id>',views.asset_view,name='asset-view'),
    path('asset-delete/<int:pk>',views.delete_asset,name='delete-asset'),
    path('lib-view/<int:lib_id>',views.liability_view,name='lib-view'),
    path('add-liability/',views.add_liability,name='add-lib'),
    path('lib-delete/<int:pk>',views.delete_lib,name='delete-lib'),
]