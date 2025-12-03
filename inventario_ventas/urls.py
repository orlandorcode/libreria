from django.urls import path, include
from .views import (
    CatalogoLibrosView, DetalleLibroPublicoView, DashboardVentasView, # ¡Importar!
    carrito_add, carrito_remove, carrito_detail, orden_checkout, orden_confirmada, carrito_update_quantity
)
from django.conf import settings
from django.conf.urls.static import static
import os

urlpatterns = [
    # Catálogo (ya existe)
    path('', CatalogoLibrosView.as_view(), name='catalogo_libros'),
    # Detalle de Libro (ya existe)
    path('libro/<int:pk>/', DetalleLibroPublicoView.as_view(), name='detalle_libro'),
    
    # --- Nuevas URLs de Carrito ---
    path('carrito/', carrito_detail, name='carrito_detail'),
    path('carrito/add/<int:libro_id>/', carrito_add, name='carrito_add'),
    path('carrito/remove/<int:libro_id>/', carrito_remove, name='carrito_remove'),
    path('carrito/update/<int:libro_id>/', carrito_update_quantity, name='carrito_update_quantity'),
    path('', CatalogoLibrosView.as_view(), name='catalogo_libros'),
    path('dashboard/', DashboardVentasView.as_view(), name='dashboard_ventas'),

    # URLs de Checkout
    path('orden/checkout/', orden_checkout, name='orden_checkout'),
    path('orden/confirmada/', orden_confirmada, name='orden_confirmada'),

    # ... otras URLs
    
]

if settings.DEBUG:
    # 1. Manejo de Archivos Estáticos (CSS, JS)
    urlpatterns += static(settings.STATIC_URL, document_root=os.path.join(settings.BASE_DIR, 'static')) 
    
    # 2. Manejo de Archivos de Medios (Imágenes de portada y black-cats.jpg)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)