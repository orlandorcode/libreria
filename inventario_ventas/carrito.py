from decimal import Decimal
from django.conf import settings
from .models import Libro

# Nombre de la clave de sesión que contendrá el carrito
CARRITO_SESSION_ID = 'carrito'

class Carrito:
    """
    Clase Carrito para gestionar la lógica de añadir,
    eliminar y calcular los totales.
    """
    def __init__(self, request):
        """Inicializa el carrito"""
        self.session = request.session
        carrito = self.session.get(CARRITO_SESSION_ID)
        
        # Si no existe carrito en la sesión, crea uno vacío
        if not carrito:
            carrito = self.session[CARRITO_SESSION_ID] = {}
            
        self.carrito = carrito

    def add(self, libro, cantidad=1):
        """Añade un libro al carrito o actualiza su cantidad."""
        libro_id = str(libro.id)
        
        # Si el libro no está en el carrito, lo añade con su precio actual
        if libro_id not in self.carrito:
            self.carrito[libro_id] = {
                'cantidad': 0,
                'precio': str(libro.precio_venta) # Almacenar como string para serialización
            }
        
        # Aumenta la cantidad
        self.carrito[libro_id]['cantidad'] += cantidad
        self.save()

    def remove(self, libro):
        """Elimina un libro completamente del carrito."""
        libro_id = str(libro.id)
        if libro_id in self.carrito:
            del self.carrito[libro_id]
            self.save()

    def __iter__(self):
        """
        Itera sobre los ítems del carrito y obtiene los libros
        desde la base de datos para mostrarlos en la vista.
        """
        libro_ids = self.carrito.keys()
        # Obtiene los objetos Libro
        libros = Libro.objects.filter(id__in=libro_ids)
        
        for libro in libros:
            libro_id = str(libro.id)
            # Copia los datos del ítem de la sesión al objeto
            self.carrito[libro_id]['libro'] = libro
            self.carrito[libro_id]['precio'] = Decimal(self.carrito[libro_id]['precio'])
            
        for item in self.carrito.values():
            # Calcula el total de la línea
            item['total_linea'] = item['precio'] * item['cantidad']
            yield item

    def __len__(self):
        """Cuenta el total de ítems (unidades de libros) en el carrito."""
        return sum(item['cantidad'] for item in self.carrito.values())

    def get_total_price(self):
        """Calcula el coste total de todos los artículos en el carrito."""
        return sum(Decimal(item['precio']) * item['cantidad'] for item in self.carrito.values())

    def clear(self):
        """Elimina el carrito de la sesión."""
        del self.session[CARRITO_SESSION_ID]
        self.save()

    def save(self):
        """Marca la sesión como modificada para asegurar que se guarde."""
        self.session.modified = True

    def get_qty(self, libro_id):
        """Devuelve la cantidad actual de un libro en el carrito."""
        libro_id = str(libro_id) # Las claves del carrito son strings
        if libro_id in self.carrito:
            # Asumiendo que el diccionario interno guarda la cantidad bajo la clave 'cantidad'
            return self.carrito[libro_id]['cantidad']
        return 0