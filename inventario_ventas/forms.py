from django import forms

class CarritoAddLibroForm(forms.Form):
    # Campo para seleccionar la cantidad (de 1 a 20 por defecto)
    cantidad = forms.IntegerField(
        min_value=1, 
        initial=1,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'style': 'width: 80px;'})
    )

class ClienteCheckoutForm(forms.Form):
    nombre = forms.CharField(max_length=50, label="Tu Nombre")
    apellido = forms.CharField(max_length=50, label="Tu Apellido")
    telefono = forms.CharField(max_length=20, label="Tu Teléfono (WhatsApp)")
    email = forms.EmailField(required=False, label="Tu Email (Opcional)")
    direccion = forms.CharField(max_length=255, label="Dirección de envío")