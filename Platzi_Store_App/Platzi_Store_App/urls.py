from django.contrib import admin
from django.urls import path, include
from products import views as product_views

urlpatterns = [
    path('admin/', admin.site.urls),

    # Ruta para la página de inicio
    path('', product_views.home, name='home'),

    # Incluye las URLs de la app 'products'
    path('products/', include('products.urls')),
    
    path('accounts/', include('accounts.urls')),
]