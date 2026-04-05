"""
URL configuration for slaughterhouseproject project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('account/',include('account.urls',namespace='account')),
    path('Customer/',include('Customer.urls',namespace='Customer')),
    path('purchase/',include('purchase.urls',namespace='purchase')),
    path('expenses/',include('expenses.urls',namespace='expenses')),
    path('Supplaier/',include('Supplaier.urls',namespace='Supplaier')),
    path('Order/',include('Order.urls',namespace='Order')),
    path('', include('Home.urls')),
    path('warehouse',include('warehouse.urls',namespace='warehouse')),
    path('product_and_catagory',include('product_and_catagory.urls',namespace='product_and_catagory')),
    path('Finance_and_Accounting',include('Finance_and_Accounting.urls',namespace='Finance_and_Accounting')),
    path('report',include('report.urls',namespace='report')),


]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

