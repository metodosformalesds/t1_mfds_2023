from django import forms
from django.db.models import fields
from .models import Producto, prestamos, PerfilEmpleado
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from creditcards.forms import CardNumberField, CardExpiryField, SecurityCodeField
from django.contrib.auth.forms import UserChangeForm, PasswordChangeForm
from django.core.exceptions import ValidationError

# Formulario para cambiar información del usuario
class UsuarioChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email')

# Formulario para cambiar la foto de perfil del usuario
class FotoPerfilForm(forms.ModelForm):
    class Meta:
        model = PerfilEmpleado
        fields = ['foto']

# Formulario para cambiar el nombre de usuario
class CambiarNombreUsuarioForm(forms.Form):
    nuevo_nombre_usuario = forms.CharField(label='Nuevo Nombre de Usuario', max_length=150)

    def clean_nuevo_nombre_usuario(self):
        nuevo_nombre_usuario = self.cleaned_data['nuevo_nombre_usuario']
        
        # Verificar si el nuevo nombre de usuario ya existe
        if User.objects.filter(username=nuevo_nombre_usuario).exists():
            raise ValidationError('El nuevo nombre de usuario ya está en uso.')
        
        return nuevo_nombre_usuario

# Formulario para registrar un nuevo usuario
class UserRegisterForm(UserCreationForm):
    email = forms.EmailField()
    password1 = forms.CharField(widget=forms.PasswordInput)
    password2 = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

# Formulario para agregar un nuevo producto
class FormProducto(forms.ModelForm):
    class Meta:
        model = Producto
        fields = ('titulo', 'imagen', 'descripcion', 'precio', 'categoria')

# Formulario para procesar pagos
class PaymentForm(forms.Form):
    nombre = forms.CharField(label='Nombre en la tarjeta', max_length=100)
    numero_tarjeta = CardNumberField(label='Número de tarjeta', max_length=16)
    fecha_vencimiento = CardExpiryField(label='Fecha de vencimiento')
    codigo_seguridad = SecurityCodeField(label='Código de seguridad (CVC)')

    def clean(self):
        cleaned_data = super().clean()
        # Puedes agregar validaciones personalizadas aquí si es necesario
        return cleaned_data

# Formulario para solicitar préstamos de empleados
class EmpleadoForm(forms.ModelForm):
    Monto = forms.CharField(max_length=100, label="Monto solicitado")
    TipoPago = forms.IntegerField(label="Sueldo a pagar")
    
    class Meta:
        model = prestamos
        fields = ['Monto', 'TipoPago']

# Formulario para realizar transferencias de empleados
class TransferForm(forms.Form):
    empleado = forms.CharField(max_length=100, label="Nombre del empleado")
    puesto = forms.CharField(max_length=100, label="Puesto que proporciona")
    sueldo = forms.DecimalField(label="Sueldo a pagar")