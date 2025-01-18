from django.urls import path
from .views import *

urlpatterns = [
    path('update-or-create-nav/', UpdateOrCreateNAVAPIView.as_view(), name='update-or-create-nav'),
    path('fetch-fund-families/', FetchFundFamiliesAPIView.as_view(), name='fetch-fund-families'),
    path('fetch-open-ended-schemes/', FetchOpenEndedSchemesAPIView.as_view(), name='fetch-open-ended-schemes'),
    path('buy-mutual-fund/', BuyMutualFundAPIView.as_view(), name='buy-mutual-fund'),
    path('sell-mutual-fund/', SellMutualFundAPIView.as_view(), name='sell-mutual-fund'),
    path('portfolio-details/', PortfolioDetailsAPIView.as_view(), name='portfolio-details'),
    path('mutual-fund/<int:mutual_fund_id>/transactions/', MutualFundTransactionsAPIView.as_view(), name='mutual-fund-transactions'),
]
