from django.contrib.auth.models import User
from sitio.forms import FormProducto
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.http.response import HttpResponse

from sitio.models import *
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.db.models import Q
from django.shortcuts import render
from .forms import PaymentForm, TransferForm,EmpleadoForm

from allauth.account.decorators import login_required
from django.db.models import Sum
from decimal import Decimal

from paypal.standard.forms import PayPalPaymentsForm
from django.conf import settings
import uuid
from django.urls import reverse
import paypalrestsdk
from datetime import datetime
from django.http import JsonResponse
from django.contrib import messages

""" 
    REGISTRO DE USUARIO
"""
def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            usuario_logeado = User.objects.last()
            #username = form.cleaned_data['username']
            messages.success(request, f"El usuario ha sido registrado exitosamente!")
            carrito = Carrito()
            carrito.usuario = usuario_logeado
            carrito.total = 0
            carrito.save()
            return redirect('SITIO:producto_index')
        else:
            messages.success(request, "No se pudo registrar el usuario, vuelva a intenarlo!")

    return render(request, 'sitio/register.html')

""" 
    PRODUCTOS
"""
def producto_index(request):
    productos = Producto.objects.all().order_by("-id")
    
    return render(request, "sitio/producto/index.html", {
        'categorias' : Categoria.objects.all(),
        'productos_top3' : productos[:3],
        'productos' : productos[3:10]
    })

# PARA ADMINS/MODERADORES
def producto_create(request):
    categorias = Categoria.objects.all()
    if request.method == "POST":
        categoria_del_producto = Categoria.objects.get(id=request.POST["categoria"])
        form = FormProducto(request.POST, request.FILES, instance=Producto(imagen=request.FILES['imagen'], categoria=categoria_del_producto))   
        if form.is_valid():
            form.save()
            return redirect("SITIO:producto_index")
            #return HttpResponse('Los campos fueron validados y aceptados!!! ' + str(categoria_del_producto))
        else:
            return render(request, 'sitio/producto/create.html', {
                'categorias' : categorias,
                'error_message' : 'Ingreso un campo incorrecto, vuelva a intentar'
            })
    else:
        return render(request, 'sitio/producto/create.html', {
            'categorias' : categorias
        })

def producto_show(request, producto_id):
    producto =  get_object_or_404(Producto, id=producto_id)

    return render(request, 'sitio/producto/show.html',{
        'categorias' : Categoria.objects.all(),
        'producto' : producto
    })

def producto_edit(request, producto_id):
    categorias = Categoria.objects.all()
    producto = Producto.objects.get(id=producto_id)

    if request.method == "POST":
        categoria_del_producto = Categoria.objects.get(id=request.POST["categoria"])
        form = FormProducto(request.POST, request.FILES, instance=Producto(imagen=request.FILES['imagen'], categoria=categoria_del_producto))   
        if form.is_valid():
            producto.titulo = request.POST['titulo']
            producto.categoria = categoria_del_producto
            producto.descripcion = request.POST['descripcion']
            producto.imagen = request.FILES['imagen']
            producto.precio = request.POST['precio']
            producto.save()
            return redirect("SITIO:producto_index")
        else:
            return render(request, 'sitio/producto/edit.html', {
                'categorias' : categorias,
                'error_message' : 'Ingreso un campo incorrecto, vuelva a intentar'
            })
    else:
        return render(request, 'sitio/producto/edit.html',{
            'categorias' : categorias,
            'producto' : producto
        })

def producto_delete(request, producto_id):
    producto = Producto.objects.get(id=producto_id)
    producto.delete()
    return redirect('SITIO:producto_index')
    #return HttpResponse(f'Eliminar producto_id: {producto.id}')

def producto_search(request):
    texto_de_busqueda = request.GET["texto"]
    productosPorTitulo = Producto.objects.filter(titulo__icontains = texto_de_busqueda).all()
    productosPorDescripcion = Producto.objects.filter(descripcion__icontains = texto_de_busqueda).all()
    productos = productosPorTitulo | productosPorDescripcion
    return render(request, 'sitio/producto/search.html',
    {
        'categorias' : Categoria.objects.all(),
        'productos' : productos,
        'texto_buscado' : texto_de_busqueda,
        'titulo_seccion' : 'Productos que contienen',
        'sin_productos' : 'No hay producto de la categoria ' + texto_de_busqueda
    })

def productos_por_categoria(request, categoria_id):
    
    #categoria = Categoria.objects.get(id=categoria_id)
    categoria = get_object_or_404(Categoria, id = categoria_id)
    productos = categoria.productos.all()
    return render(request, 'sitio/producto/search.html',
    {
        'categorias' : Categoria.objects.all(),
        'productos' : productos,
        'categoria' : categoria.descripcion,
        'titulo_seccion' : 'Productos de la categoria',
        'sin_productos' : 'No hay producto de la categoria ' + categoria.descripcion
    })

""" 
    CARRITO
"""
@login_required
def carrito_index(request):
    categorias = Categoria.objects.all()
    usuario_logeado = request.user

    try:
        carrito = Carrito.objects.get(usuario=usuario_logeado)
        items_carrito = carrito.items.all()
        nuevo_precio_Carrito = items_carrito.aggregate(total=Sum('producto__precio'))['total']
    except Carrito.DoesNotExist:
        carrito = None
        items_carrito = []
        nuevo_precio_Carrito = 0

    if carrito:
        carrito.total = nuevo_precio_Carrito
        carrito.save()

    return render(request, 'sitio/carrito/index.html', {
        'categorias': categorias,
        'usuario': usuario_logeado,
        'items_carrito': items_carrito
    })

def carrito_save(request):
    #tieneCarrito = Carrito.objects.filter(usuario=8).count()
    # Devuelve un 404 si no encuentra el carrito
    #arrito = get_object_or_404(Carrito, usuario=usuario_logeado.id)

    usuario_logeado = request.user
    producto_id = request.POST.get('producto_id')
    
    if not producto_id:
        return redirect("SITIO:producto_index")
    
    producto = get_object_or_404(Producto, pk=producto_id)

    try:
        carrito = Carrito.objects.get(usuario=usuario_logeado)
    except Carrito.DoesNotExist:
        carrito = Carrito.objects.create(usuario=usuario_logeado, total=Decimal('0.00'))

    item_carrito, created = Carrito_item.objects.get_or_create(carrito=carrito, producto=producto)

    if carrito.total is None:
        carrito.total = Decimal('0.00')

    if created:
        carrito.total += producto.precio
        carrito.save()
        messages.success(request, f"El producto {producto.titulo} fue agregado al carrito")
    else:
        messages.warning(request, f"El producto {producto.titulo} ya está en el carrito")

    return redirect("SITIO:producto_index")

def carrito_clean(request):
    usuario_logeado = request.user

    try:
        carrito = Carrito.objects.get(usuario=usuario_logeado)
    except Carrito.DoesNotExist:
        carrito = Carrito.objects.create(usuario=usuario_logeado, total=0)  # Inicializar total a 0

    carrito.items.all().delete()
    carrito.total = 0
    carrito.save()

    return redirect('SITIO:carrito_index')

def item_carrito_delete(request, item_carrito_id):
    item_carrito = Carrito_item.objects.get(id=item_carrito_id)
    carrito = item_carrito.carrito
    
    # Vuelvo a calcular el precio del carrito
    nuevo_precio_Carrito = 0 - item_carrito.producto.precio
    for item in carrito.items.all():
        nuevo_precio_Carrito += item.producto.precio

    # Realizo los cambios en la base de datos
    carrito.total = nuevo_precio_Carrito
    item_carrito.delete()
    carrito.save()
    return redirect("SITIO:carrito_index")
    #return HttpResponse(f'Carrito_id: {carrito.id} Total: {carrito.total} | Item_carrito: {item_carrito} | Precio: {precio_item}')

"""
    PAGINAS
"""
def acerca_de(request):
    return render(request, 'sitio/paginas/acerca_de.html',{
        'categorias' : Categoria.objects.all(),
    })
    
    
def nominas(request):
    datos = empleados.objects.all()
    usuario=request.user
 
    

    
  
    if request.method == 'POST':
         
        
        # Obten los datos enviados en el formulario (suponiendo que 'datos' es una lista de nombres)
         datos  = request.POST.getlist('datos')
         datos = datos[0]
      
    
    # Realiza la consulta filtrando por los nombres en la lista 'datos'
         datos = empleados.objects.filter(Nombre=usuario,id=datos)

         return render(request, 'sitio/nominas/transferenciaNomina.html', {'datos': datos})
    else:
       
        return render(request, 'sitio/nominas/nomina.html', {'datos': datos})
        
   

def SolicitarNomina(request):
    if request.method == 'POST':
        form = TransferForm(request.POST)
    return render(request, 'sitio/nominas/TransferenciaNomina.html', {'form': form})
    

def Aceptarprestamo(request):
     datos = prestamos.objects.all()
    
     

     if request.method == 'POST':
         
        
        # Obten los datos enviados en el formulario (suponiendo que 'datos' es una lista de nombres)
         datos  = request.POST.getlist('datos')
         datos = datos[0]
         
            # Obten los datos enviados en el formulario (suponiendo que 'datos' es una lista de IDs)
         dato_ids = request.POST.getlist('datos')

         for dato_id in dato_ids:
            # Filtra el objeto prestamos por ID
            dato = prestamos.objects.get(id=dato_id)

            # Obtén la fecha límite del objeto
            fecha_limite = dato.FechaLimite

            # Verifica si la fecha actual es superior a la fecha límite
            if datetime.now().date() > fecha_limite:
                # Realiza la operación de eliminación
                dato.delete()
                messages.success(request, 'ya paso de la fecha limite para ser aceptado el prestamo')
                return redirect('SITIO:producto_index')
      
    
    # Realiza la consulta filtrando por los nombres en la lista 'datos'
         datos = prestamos.objects.filter(id=datos)

         return render(request, 'sitio/prestamos/transferenciaPrestamo.html', {'datos': datos})
     else:
       
        return render(request, 'sitio/prestamos/prestamos.html', {'datos': datos})
        
        
def transferenciaPrestamo(request):
    if request.method == 'POST':
        form = EmpleadoForm(request.POST)
    return render(request, 'sitio/nominas/transferenciaPrestamo.html', {'form': form})
    
def SolicitarPrestamo(request):
    
    
    if request.method == 'POST':
        Monto = request.POST['Monto']
      
        FechaLimite = request.POST['FechaLimite']
        
        # Convierte la fecha a un objeto Date
        fecha_limite = datetime.strptime(FechaLimite, '%Y-%m-%d').date()
        nombre=request.user
        
      

        

        prestamo = prestamos(nombre=nombre,Monto=Monto,FechaLimite=fecha_limite)
        prestamo.save()  # Guarda los datos en la base de datos
        return redirect('SITIO:Prestamosolicitado')  # Redirige a la página que desees después de guardar el préstamo

    return render(request, 'sitio/prestamos/SolicitarPrestamo.html')

def Prestamosolicitado(request):
    return render(request,'sitio/prestamos/prestamoSolicitado.html')



def proceso_pago(request):
    
    if request.method == 'POST':
        form = PaymentForm(request.POST)
        """if form.is_valid():
            # Procesa el pago aquí
            # Guarda los datos en la base de datos, realiza una solicitud a una pasarela de pago, etc.
            # Redirige a una página de confirmación o realiza otras acciones
            """
    else:
       form = PaymentForm()
    categorias = Categoria.objects.all()
    usuario_logeado = User.objects.get(username=request.user)
    productos = Carrito.objects.get(usuario=usuario_logeado.id).items.all()

    carrito = Carrito.objects.get(usuario=usuario_logeado.id)
    nuevo_precio_Carrito = 0
    for item in carrito.items.all():
        nuevo_precio_Carrito += item.producto.precio
    carrito.total = nuevo_precio_Carrito
    carrito.save()
    host= request.get_host()
    paypal_checkout={
        'business': settings.PAYPAL_RECEIVER_EMAIL,
        'amount':Producto.precio,
        'item_name': Producto.titulo,
        'invoice':uuid.uuid4(),
        'currency_code': 'USD',
        'notify_url': f"https://{host}{reverse('paypal-ipn')}"
        
    }
    paypal_payment=PayPalPaymentsForm(initial=paypal_checkout)
    

    return render(request, 'sitio/Tarjeta/TarjetaCarrito.html', {'form': form,'categorias' : categorias,'usuario' : usuario_logeado,'items_carrito' : productos,'paypal':paypal_payment})


def perfil(request):
    
    usuario=request.user
    
    
    return render(request,'sitio/perfil/usuario.html', {'usuario':usuario})
    
    
  
def perfilempleado(request):
    
    usuario=request.user
    
    
    return render(request,'sitio/perfil/empleado.html', {'usuario':usuario})
    
    
    
 
def perfiladmin(request):
    
    usuario=request.user
    
    
    return render(request,'sitio/perfil/admin.html', {'usuario':usuario})
    
    
    
    
    
   
    
  
    
    



