from django import forms
from django.db.models import fields
from .models import Producto
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from creditcards.forms import CardNumberField, CardExpiryField, SecurityCodeField

class UserRegisterForm(UserCreationForm):
    email = forms.EmailField()
    password1 = forms.CharField(widget=forms.PasswordInput)
    password2 = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

""" 
    PRODUCTO 
"""
class FormProducto(forms.ModelForm):

    class Meta:
        model = Producto
        fields = ('titulo','imagen','descripcion','precio','categoria')
        """ widgets = {
            'titulo': forms.TextInput(),
            'descripcion' : forms.Textarea(),
            'precio' : forms.NumberInput(),
            'imagen' : forms.FileField()
        } """
        """ widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-control', 'placeholder':'Ingrese el nombre del producto...' , 'required': True}),
            'descripcion' : forms.Textarea(attrs={'class' : 'form-control', 'row' : 3, 'required': True}),
            'precio' : forms.NumberInput(attrs={'class' : 'form-control', 'placeholder':'XXXX.XX', 'required': True}),
            'imagen' : forms.FileField(attrs={'class':'form-control-file', 'id':'imagen', 'placeholder': 'Ingrese la imagen...', 'required': True})
        } """

class PaymentForm(forms.Form):
    nombre = forms.CharField(label='Nombre en la tarjeta', max_length=100)
    numero_tarjeta = CardNumberField(label='Número de tarjeta', max_length=16)
    fecha_vencimiento = CardExpiryField(label='Fecha de vencimiento')
    codigo_seguridad = SecurityCodeField(label='Código de seguridad (CVC)')

    def clean(self):
        cleaned_data = super().clean()
        numero_tarjeta = cleaned_data.get('numero_tarjeta')
        fecha_vencimiento = cleaned_data.get('fecha_vencimiento')
        codigo_seguridad = cleaned_data.get('codigo_seguridad')

        # Puedes agregar validaciones personalizadas aquí si es necesario

        return cleaned_data
    
    
class SolicitarPrestamo(forms.Form):
    DineroProporcionado=forms.IntegerField(label="Cuanto quieres que te prestemos?")
    
    
class TransferForm(forms.Form):
    empleado = forms.CharField(max_length=100, label="Nombre del empleado")
    puesto = forms.CharField(max_length=100, label="Puesto que proporciona")
    sueldo = forms.DecimalField(label="Sueldo a pagar")