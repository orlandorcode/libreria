
# Create your models here.

from django.db import models
from django.db.models import Sum, F

# --- 1. Modelos de Entidades de Soporte (Maestros) ---

class Tienda(models.Model):
    id = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=50, verbose_name="Nombre de la Tienda", null=False)
    lugar = models.CharField(max_length=50, verbose_name="Ubicación", null=True, blank=True)

    class Meta:
        verbose_name = "Tienda/Sucursal"
        verbose_name_plural = "Tiendas/Sucursales"

    def __str__(self):
        return self.nombre

class Editorial(models.Model):
    id = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=40, verbose_name="Nombre de Editorial", null=False)
    telefono = models.CharField(max_length=40, verbose_name="Teléfono de Contacto", null=False)
    email = models.CharField(max_length=40, verbose_name="Email de Contacto", null=True, blank=True)

    def __str__(self):
        return self.nombre

class Bodega(models.Model):
    id = models.AutoField(primary_key=True)
    nota = models.CharField(max_length=255, verbose_name="Descripción de la Bodega", null=False)
    
    def __str__(self):
        return f"Bodega {self.id} ({self.nota[:25]}...)"

# --- 2. Modelos de Personas ---

class Staff(models.Model):
    id = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=20, verbose_name="Nombre", null=False)
    apellido = models.CharField(max_length=20, verbose_name="Apellido", null=False)
    # Si la tienda se elimina, el staff puede quedar sin tienda (null=True)
    tienda = models.ForeignKey(Tienda, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Tienda Asignada")

    class Meta:
        verbose_name_plural = "Staff"

    def __str__(self):
        return f"{self.nombre} {self.apellido}"

class Cliente(models.Model):
    id = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=20, verbose_name="Nombre", null=False)
    apellido = models.CharField(max_length=20, verbose_name="Apellido", null=False)
    telefono = models.CharField(max_length=20, verbose_name="Teléfono", null=False)
    email = models.CharField(max_length=40, verbose_name="Email", null=True, blank=True)
    # auto_now_add=True registra la fecha solo al crearse
    fecha_ingreso = models.DateField(verbose_name="Fecha de Ingreso", auto_now_add=True)

    def __str__(self):
        return f"{self.nombre} {self.apellido}"

# --- 3. Modelos de Producto e Inventario ---

class Libro(models.Model):
    id = models.AutoField(primary_key=True)
    # on_delete=models.PROTECT evita que se elimine una editorial si tiene libros asociados
    editorial = models.ForeignKey(Editorial, on_delete=models.PROTECT, verbose_name="Editorial", null=False)
    nombre = models.CharField(max_length=40, verbose_name="Título", null=False)
    autor = models.CharField(max_length=40, verbose_name="Autor", null=False)
    ilustrador = models.CharField(max_length=40, verbose_name="Ilustrador", null=True, blank=True)
    # Usar DecimalField para dinero en lugar de INT
    costo = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Costo de Adquisición", null=False)
    precio_venta = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Precio de Venta", null=False)
    # BinaryField para BLOB de la imagen (podrías usar ImageField si configuras almacenamiento)
    portada = models.ImageField(
            upload_to= 'portadas/', #Las imágenes se guardarán en media/portadas/
            blank=True, 
            null=True)
    sinopsis = models.TextField(verbose_name='Sinópsis del Libro', null = True, blank = True)


    def __str__(self):
        return self.nombre
    
    # Propiedad calculada para mostrar el stock total en el admin/vistas
    @property
    def stock_total(self):
        # Suma la cantidad de stock a través de la relación inversa 'stock_set'
        return self.stock_set.aggregate(total=Sum('cantidad'))['total'] or 0

class Stock(models.Model):
    # Relación N:M, usa las FK como claves para garantizar unicidad (unique_together)
    libro = models.ForeignKey(Libro, on_delete=models.CASCADE, verbose_name="Libro", null=False)
    bodega = models.ForeignKey(Bodega, on_delete=models.CASCADE, verbose_name="Bodega", null=False)
    cantidad = models.IntegerField(verbose_name="Cantidad en Stock", null=False)
    
    class Meta:
        # Asegura que un libro solo pueda estar una vez en una bodega específica
        unique_together = ('libro', 'bodega')
        verbose_name_plural = "Stock"


# --- 4. Modelos de Transacción (Ventas) ---

class Venta(models.Model):

    ESTADO_CHOICES = [
        ('PENDIENTE', 'Pendiente de Confirmación'), # Estado inicial
        ('CONFIRMADA', 'Confirmada y Procesada'),  # Venta completada y stock descontado
        ('CANCELADA', 'Cancelada'),]

    id = models.AutoField(primary_key=True)
    cliente = models.ForeignKey('Cliente', on_delete=models.SET_NULL, verbose_name="Cliente", null=True)
    staff = models.ForeignKey('Staff', on_delete=models.SET_NULL, verbose_name="Vendedor", null=True)
    # Este campo DEBE coincidir con la suma de los detalles para auditoría
    precio_total = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Total de Venta", null=False)
    # auto_now_add es el equivalente a DEFAULT(NOW) en la base de datos
    fecha_hora = models.DateTimeField(auto_now_add=True, verbose_name="Fecha y Hora", null=False)
    
    
    # NUEVO CAMPO DE ESTADO
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default='PENDIENTE', # Estado por defecto al crear
        verbose_name="Estado de la Venta"
    )

    def save(self, *args, **kwargs):
        # 1. Si la venta se acaba de cambiar a CONFIRMADA, descontamos stock.
        # Solo descontamos si el estado PREVIO era 'PENDIENTE'.
        if self.pk:
            venta_previa = Venta.objects.get(pk=self.pk)
            
            if venta_previa.estado == 'PENDIENTE' and self.estado == 'CONFIRMADA':
                
                # Descuento atómico de stock
                with transaction.atomic():
                    bodega_principal = Bodega.objects.get(id=1) # Asumimos Bodega ID 1
                    
                    for detalle in self.detalleventa_set.all():
                        Stock.objects.create(
                            libro=detalle.libro,
                            bodega=bodega_principal,
                            cantidad=-detalle.cantidad, # CANTIDAD NEGATIVA para restar
                            nota=f"Venta confirmada #{self.id}"
                        )
                print(f"✅ Stock descontado para la Venta #{self.id}")

        super().save(*args, **kwargs) # Llama al método save original

    class Meta:
        verbose_name_plural = "Ventas"

    def __str__(self):
        return f"Venta #{self.id} - Total: {self.precio_total}"
    
    # Método para calcular el total de la venta (útil antes de guardar)
    @property
    def total_calculado(self):
        # Usamos Coalesce para tratar valores NULL (de inlines vacíos) como 0 antes de la multiplicación
        return self.detalleventa_set.aggregate(
            total=Sum(
                Coalesce(F('cantidad'), 0) * Coalesce(F('precio'), 0) # <<< ¡Corrección clave aquí!
            )
        )['total'] or 0

class DetalleVenta(models.Model):
    id = models.AutoField(primary_key=True)
    venta = models.ForeignKey(Venta, on_delete=models.CASCADE, verbose_name="Venta", null=False)
    libro = models.ForeignKey(Libro, on_delete=models.PROTECT, verbose_name="Libro Vendido", null=False)
    cantidad = models.IntegerField(verbose_name="Cantidad", null=False)
    precio = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Precio Unitario Vendido", null=False)
    fecha_hora = models.DateTimeField(auto_now_add=True, verbose_name="Fecha y Hora de Registro", null=False)

    class Meta:
        verbose_name = "Detalle de Venta"
        verbose_name_plural = "Detalle de Ventas"

    def __str__(self):
        return f"Venta {self.venta.id} | {self.libro.nombre} ({self.cantidad} uds)"

    # PROPIEDAD CORREGIDA: Maneja valores None (vacíos)
    @property
    def total_linea(self):
        # Si la cantidad o el precio es None (está vacío en el formulario), se usa 0.
        cantidad = self.cantidad if self.cantidad is not None else 0
        precio = self.precio if self.precio is not None else 0
        
        # Además, aseguramos que el tipo de datos sea Decimal/entero para la multiplicación
        # (Aunque deberían serlo, es buena práctica)
        try:
            return cantidad * precio
        except TypeError:
            return 0.00
