from django.urls import path
from .views import (
    CatalogoLibrosView, DetalleLibroPublicoView, DashboardVentasView, # ¡Importar!
    carrito_add, carrito_remove, carrito_detail, orden_checkout, orden_confirmada, carrito_update_quantity
)

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