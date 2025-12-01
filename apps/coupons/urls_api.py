# apps/coupons/urls_api.py

from django.urls import path
from . import api_views

app_name = "coupons_api"

urlpatterns = [
    path("validate/", api_views.CouponValidateAPIView.as_view(), name="validate"),
    path("apply/", api_views.CouponApplyAPIView.as_view(), name="apply"),
    path("remove/", api_views.CouponRemoveAPIView.as_view(), name="remove"),
    path("available/", api_views.UserAvailableCouponsAPIView.as_view(), name="available"),
    path("usages/", api_views.UserCouponUsagesAPIView.as_view(), name="usages"),
]
