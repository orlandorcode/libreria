from django.views.generic import ListView, DetailView, TemplateView 
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from django.db import transaction, DatabaseError
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin

# Importaciones necesarias para la solución
from django.db.models import Sum, Q, F, DecimalField # <<< ¡Importa DecimalField!
from django.db.models.functions import Coalesce 
from datetime import date, timedelta
from decimal import Decimal # <<< ¡Importa Decimal!

import urllib.parse

from .models import Libro, Cliente, Venta, DetalleVenta, Cliente , Stock, Staff
from .carrito import Carrito
from .forms import CarritoAddLibroForm, ClienteCheckoutForm

# --- Vistas del Catálogo Público (Paso 3) ---

class CatalogoLibrosView(ListView):
    model = Libro
    template_name = 'catalogo/lista_libros.html' 
    context_object_name = 'libros'
    # paginate_by = 12 

    def get_queryset(self):
        queryset = super().get_queryset().annotate(
            stock_disponible=Coalesce(Sum('stock__cantidad'), 0)
        ).filter(
            stock_disponible__gt=0
        )
        query = self.request.GET.get('q')
        if query:
            queryset = queryset.filter(
                Q(nombre__icontains=query) | 
                Q(autor__icontains=query) |  
                Q(editorial__nombre__icontains=query)
            )
        return queryset.order_by('nombre')


class DetalleLibroPublicoView(DetailView):
    model = Libro
    template_name = 'catalogo/detalle_libro_publico.html' 
    context_object_name = 'libro'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # El stock total se calcula automáticamente por el @property en el modelo.
        context['stock'] = self.object.stock_total
        # Añade la instancia del formulario al contexto para el botón "Añadir al Carrito"
        context['form'] = CarritoAddLibroForm() 
        return context


# --- Vistas para Manejar el Carrito (Paso 4) ---

@require_POST
def carrito_add(request, libro_id):
    """Añade un libro al carrito (vista de acción POST)"""
    carrito = Carrito(request)
    libro = get_object_or_404(Libro, id=libro_id)
    form = CarritoAddLibroForm(request.POST)

    if form.is_valid():        
        # 1. Obtener la cantidad solicitada (Asegurarse de que sea un entero positivo)
        try:
            cantidad_solicitada = int(request.POST.get('cantidad', 1))
            if cantidad_solicitada <= 0:
                raise ValueError
        except ValueError:
            messages.error(request, 'La cantidad debe ser un número entero positivo.')
            return redirect('detalle_libro', pk=libro_id)
        
        # 2. Obtener el stock disponible (Debes tener una propiedad o función para esto)
        # Asumiendo que tienes una propiedad en Libro llamada 'stock_total' o 'stock_disponible'
        # o que tienes una forma de calcularlo aquí:
        
        # --- Lógica de cálculo de stock (Ajusta esto a cómo calculas el stock real) ---
        stock_real_disponible = libro.stock_total # << USAR TU FUNCIÓN/PROPIEDAD DE STOCK TOTAL
        
        cantidad_actual_en_carrito = carrito.get_qty(libro.id)

        # 3. Calcular la nueva cantidad total
        nueva_cantidad_total = cantidad_actual_en_carrito + cantidad_solicitada
        
        # --- FIN Lógica de cálculo de stock ---
        

        # 3. CRÍTICO: VALIDACIÓN DEL SERVIDOR
        if nueva_cantidad_total > stock_real_disponible:
            # Calcular cuánto más se puede agregar
            cantidad_maxima_a_agregar = stock_real_disponible - cantidad_actual_en_carrito
            
            # Si la cantidad supera el stock, enviamos un mensaje de error
            # Si la nueva cantidad supera el stock, emitir error
            messages.error(
                request, 
                f'Error: El stock de "{libro.nombre}" es de {stock_real_disponible} unidades. '
                f'Ya tienes {cantidad_actual_en_carrito} en el carrito, solo puedes añadir {cantidad_maxima_a_agregar} más.'
            )            # Redirigimos de vuelta a la página de detalle del libro
            return redirect('detalle_libro', pk=libro_id)
        
        # 4. Si la validación es exitosa, añadir al carrito
        carrito.add(libro, cantidad=cantidad_solicitada)
        messages.success(request, f'{cantidad_solicitada}x {libro.nombre} se añadió al carrito correctamente. Cantidad total: {nueva_cantidad_total}.')
        
        return redirect('carrito_detail') # Redirigir a la página del carrito (o donde desees)

    return redirect('detalle_libro', pk=libro_id) 

@require_POST
def carrito_remove(request, libro_id):
    """Elimina un libro del carrito."""
    carrito = Carrito(request)
    libro = get_object_or_404(Libro, id=libro_id)
    carrito.remove(libro)    
    return redirect('carrito_detail')

def carrito_detail(request):
    """Muestra el contenido del carrito."""
    carrito = Carrito(request)
    # Pasa el formulario del cliente al contexto
    checkout_form = ClienteCheckoutForm() 
    return render(request, 'catalogo/carrito_detail.html', {
        'carrito': carrito,
        'checkout_form': checkout_form # <<< Pasa el formulario
    })

class DashboardVentasView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard/dashboard_ventas.html'

    # Puedes añadir una URL de login si no usas la predeterminada '/accounts/login/'
    login_url = '/admin/login/'

    def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            
            hoy = date.today()
            hace_7_dias = hoy - timedelta(days=7)

            # 2. Métrica 1: Ventas Totales y Ventas de Hoy
            ventas_totales_hoy = Venta.objects.filter(fecha_hora__date=hoy).aggregate(
                # 1. Definir el tipo de salida como Decimal
                total=Sum('precio_total', output_field=DecimalField()) 
            )['total'] or Decimal('0.00') # 2. Usar Decimal('0.00') como default

            ventas_totales_semana = Venta.objects.filter(fecha_hora__date__gte=hace_7_dias).aggregate(
                total=Sum('precio_total', output_field=DecimalField())
            )['total'] or Decimal('0.00') # 2. Usar Decimal('0.00') como default

            context['ventas_hoy'] = f"{ventas_totales_hoy:.2f}"
            context['ventas_semana'] = f"{ventas_totales_semana:.2f}"
            
            # 3. Métrica 2: Clientes Top (Basado en gasto)
            clientes_top = Cliente.objects.annotate(
                # 1. Definir el tipo de salida del Sum y Coalesce
                gasto_total=Coalesce(
                    Sum('venta__precio_total', output_field=DecimalField()), 
                    Decimal('0.00') # 2. Usar Decimal('0.00') como default
                )
            ).order_by('-gasto_total')[:5]

            context['clientes_top'] = clientes_top
            
            # ... (Las métricas 4 y 5 de libros vendidos y stock no usan decimales, por lo que quedan igual)
            
            return context
    
@transaction.atomic
def orden_checkout(request):
    """
    Captura los datos del cliente, registra la Venta como PENDIENTE
    y guarda la info del cliente en la sesión.
    """
    carrito = Carrito(request)
    if not carrito:
        messages.error(request, "El carrito está vacío.")
        return redirect('carrito_detail')

    if request.method == 'POST':
        form = ClienteCheckoutForm(request.POST)
        if form.is_valid():
            datos_cliente = form.cleaned_data

            try:
            
                # 1. CREAR EL ENCABEZADO DE LA VENTA COMO PENDIENTE
                nueva_venta = Venta.objects.create(
                    # Estos campos se dejarán NULL o con valores temporales.
                    # Asegúrate que tus modelos permitan id_cliente, id_staff ser NULL.
                    # Si no pueden ser NULL, DEBES DEJAR ESTA FUNCIÓN PENDIENTE
                    # HASTA QUE MODIFIQUES TUS MIGRACIONES para permitir NULL.
                    
                    # Para fines de prueba, pondremos ID_CLIENTE=NULL, ID_STAFF=NULL. 
                    # Si tienes restricciones NOT NULL en el modelo, comenta estas líneas.
                    cliente=None, 
                    staff=None,
                    
                    precio_total=carrito.get_total_price(),
                    estado = 'PENDIENTE'

                )
                
                # Guardamos los datos temporales del cliente en la sesión para el mensaje de WhatsApp
                
                # Opción más simple: Usar la sesión para el mensaje de WhatsApp.
                request.session['temp_cliente_info'] = datos_cliente
                

                # 2. CREAR DETALLES DE VENTA
                for item in carrito:

                    libro = item['libro']
                    cantidad_vendida = item['cantidad']

                    DetalleVenta.objects.create(
                        venta=nueva_venta,
                        libro=libro,
                        cantidad=cantidad_vendida,
                        precio=item['precio']
                    )


                # 3. LIMPIAR CARRITO Y REDIRIGIR A CONFIRMACIÓN
                carrito.clear()
                request.session['last_order_id'] = nueva_venta.id 

                datos_cliente = {
                    'nombre': f"{datos_cliente['nombre']} {datos_cliente['apellido']}",
                    'telefono': datos_cliente['telefono'],
                    'email': datos_cliente['email'],
                    # Agregamos un campo de dirección al contexto temporal.
                    'direccion': request.POST.get('direccion', 'No especificada') 
                }
                request.session['temp_cliente_info'] = datos_cliente

                messages.success(request, f"¡Orden #{nueva_venta.id} recibida! Por favor, contacte por WhatsApp para finalizar.")
                return redirect('orden_confirmada')
        
            except DatabaseError as e:
                # Si ocurre un error de stock/DB, la transacción se revierte automáticamente
                messages.error(request, f"Lo sentimos, hubo un error con el inventario. Por favor, revisa tu carrito. ({e})")
                return redirect('carrito_detail')

        else:
            # Si el formulario no es válido
            messages.error(request, "Por favor, corrige los errores del formulario de contacto (Nombre, Teléfono, Dirección).")
            return redirect('carrito_detail')


def orden_confirmada(request):
    """Muestra la página final de confirmación y prepara el link de WhatsApp."""
    
    order_id = request.session.pop('last_order_id', None)
    datos_cliente_temp = request.session.pop('temp_cliente_info', {}) # <<< Obtener datos de cliente

    if not order_id:
        return render(request, 'catalogo/orden_confirmada.html', {'order_id': None})
        
    try:
        venta = Venta.objects.get(id=order_id)
        detalles = venta.detalleventa_set.all()
    except Venta.DoesNotExist:
        messages.error(request, "La orden solicitada no existe.")
        return redirect('catalogo_libros')

    # CONSTRUIR EL MENSAJE DETALLADO
    mensaje_partes = [
        f"¡Hola! He generado una Orden *PENDIENTE* *#{venta.id}*.",
        f"Mis datos de contacto son:",
        f"Nombre: {datos_cliente_temp.get('nombre', 'N/A')} {datos_cliente_temp.get('apellido', '')}",
        f"Teléfono: {datos_cliente_temp.get('telefono', 'N/A')}",
        f"Email: {datos_cliente_temp.get('email', 'N/A')}",
        f"Dirección de Envío: {datos_cliente_temp.get('direccion', 'N/A')}",
        "\n--- Detalle del Pedido ---"
    ]
    
    for item in detalles:
        linea = f"• {item.libro.nombre} (x{item.cantidad}) | P/U: ${item.precio}"
        mensaje_partes.append(linea)

    mensaje_partes.append(f"\n*SUBTOTAL (+ envío): ${venta.precio_total:.2f}*")
    mensaje_partes.append("\nPor favor, confirme mi pedido y los pasos para el pago y envío.")
    
    mensaje_base = "\n".join(mensaje_partes)
    
    mensaje_codificado = urllib.parse.quote(mensaje_base)
    
    numero_whatsapp = "+525620576697" 
    
    whatsapp_url = f"https://wa.me/{numero_whatsapp}?text={mensaje_codificado}"
    
    context = {
        'order_id': venta.id,
        'whatsapp_url': whatsapp_url,
        'venta': venta,
        'datos_cliente': datos_cliente_temp
    }
    
    return render(request, 'catalogo/orden_confirmada.html', context)
