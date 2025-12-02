from django.contrib import admin
from django.utils.html import format_html # <<< Importar para el HTML

# Register your models here.

from .models import (
    Tienda, Editorial, Bodega, Staff, Cliente, 
    Libro, Stock, Venta, DetalleVenta
)

# --- INLINE para Stock ---

# 1. Permite administrar el Stock de un libro directamente en la página de Libro.
class StockInline(admin.TabularInline):
    model = Stock
    extra = 1  # Muestra un campo vacío adicional para agregar nuevo stock

# --- Administrador del Libro (Custom) ---

class LibroAdmin(admin.ModelAdmin):
    # Campos que se muestran en la vista de lista (tabla principal)
    list_display = (
        'nombre', 
        'autor', 
        'editorial', 
        'precio_venta', 
        'stock_total_display', # Campo calculado
        'mostrar_portada' # <<< Añade la miniatura aquí
    )
    # Filtros laterales
    list_filter = ('editorial', 'autor')
    # Campos de búsqueda
    search_fields = ('nombre', 'autor', 'editorial__nombre')
    
    # El inline que inyecta la tabla Stock en el formulario de Libro
    inlines = [StockInline] 
    
    # Define la columna calculada para mostrar el stock total
    def stock_total_display(self, obj):
        return obj.stock_total
    stock_total_display.short_description = 'Stock Total'

    def mostrar_portada(self, obj):
        if obj.portada:
            # Usa format_html para inyectar código HTML seguro
            return format_html('<img src="{}" style="width: 50px; height: auto; border-radius: 4px;" />', obj.portada.url)
        return "Sin portada"
    
    mostrar_portada.short_description = 'Portada' # Nombre de la columna en el admin    

admin.site.register(Libro, LibroAdmin)
# --- INLINE para Detalle de Venta ---

# 2. Permite administrar los DetalleVenta directamente en la página de Venta.
class DetalleVentaInline(admin.TabularInline):
    model = DetalleVenta
    readonly_fields = ('total_linea',)
    extra = 1

# --- Administrador de la Venta (Custom) ---

@admin.register(Venta)
class VentaAdmin(admin.ModelAdmin):
    list_display = ('id', 'fecha_hora', 'cliente', 'staff', 'precio_total', 'total_calculado_display')
    list_filter = ('fecha_hora', 'staff')
    search_fields = ('cliente__nombre', 'cliente__apellido', 'staff__nombre')
    inlines = [DetalleVentaInline]
    # Hace el precio_total readonly y lo calcularemos antes de guardar
    readonly_fields = ('precio_total',) 

    # Muestra el total calculado antes de guardar (para comparación)
    def total_calculado_display(self, obj):
        return f"{obj.total_calculado:.2f}"
    total_calculado_display.short_description = 'Total Calculado'

# --- Registro de Modelos Simples ---

# 3. Modelos sin personalización avanzada, simplemente se registran.
admin.site.register(Tienda)
admin.site.register(Editorial)
admin.site.register(Bodega)
admin.site.register(Staff)
admin.site.register(Cliente)

# Stock no se registra solo porque se administra desde Libro
