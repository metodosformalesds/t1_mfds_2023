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
from .forms import PaymentForm, TransferForm,EmpleadoForm,CambiarNombreUsuarioForm

from allauth.account.decorators import login_required
from django.db.models import Sum
from decimal import Decimal

from paypal.standard.forms import PayPalPaymentsForm
from django.conf import settings
import uuid
from django.urls import reverse

from datetime import datetime
from django.http import JsonResponse
from django.contrib import messages
from django.shortcuts import render, redirect
from .forms import FotoPerfilForm
from PIL import Image

from paypal.standard.forms import PayPalPaymentsForm
from django.conf import settings
import uuid
from django.urls import reverse
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
            # The above code is redirecting the user to the 'producto_index' page in the 'SITIO'
            # application.
            return redirect('SITIO:producto_index')
        else:
            messages.success(request, "No se pudo registrar el usuario, vuelva a intenarlo!")

    return render(request, 'sitio/register.html')


def logout(request):
    return render(request,'sitio/logged_out.html')
""" 
    PRODUCTOS
"""


def producto_index(request):
    # El código anterior recupera todas las instancias del modelo "Producto" de la base de datos y
    # ordenarlos en orden descendente según su atributo "id".
    productos = Producto.objects.all().order_by("-id")
    
    return render(request, "sitio/producto/index.html", {
        'categorias' : Categoria.objects.all(),
        'productos_top3' : productos[:3],
        'productos' : productos[3:10]
    })

# PARA ADMINS/MODERADORES
def producto_create(request):
    #agarramos los datos de la categoria
    categorias = Categoria.objects.all()
    if request.method == "POST":
        # El código anterior maneja una solicitud POST. Primero recupera la categoría seleccionada
        categoria_del_producto = Categoria.objects.get(id=request.POST["categoria"])
         # producto de los datos de la solicitud. Luego, crea una instancia del formulario FormProducto
        form = FormProducto(request.POST, request.FILES, instance=Producto(imagen=request.FILES['imagen'], categoria=categoria_del_producto))   
        # Datos POST y la categoría seleccionada. Si el formulario es válido, guarda los datos del formulario
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
           # recuperar los valores de los campos del formulario (titulo, descripcion, imagen, precio)
            producto.titulo = request.POST['titulo']
            producto.categoria = categoria_del_producto
            producto.descripcion = request.POST['descripcion']
            producto.imagen = request.FILES['imagen']
            producto.precio = request.POST['precio']
            # asignándolos a los atributos correspondientes de un objeto "producto". Luego, se guarda
            producto.save()
            # el objeto a la base de datos y redirige al usuario a la página "producto_index".
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
    # la entrada de texto del diccionario request.GET. Luego, utiliza la búsqueda `icontains` para filtrar el
    texto_de_busqueda = request.GET["texto"]
  # Objetos `Producto` según si los campos `titulo` o `descripcion` contienen el texto dado.
    productosPorTitulo = Producto.objects.filter(titulo__icontains = texto_de_busqueda).all()
    productosPorDescripcion = Producto.objects.filter(descripcion__icontains = texto_de_busqueda).all()
    # Finalmente, combina los resultados de ambos filtros usando el operador `|` y asigna el resultado
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
    # Obtener todas las categorías
    categorias = Categoria.objects.all()
    #Obtener el usuario logeado
    usuario_logeado = request.user
    #Inicializador de la variable
    total=0
    try:
        carrito = Carrito.objects.get(usuario=usuario_logeado)
        items_carrito = carrito.items.all()
        # Calcular el nuevo precio total del carrito sumando los precios de los productos
        nuevo_precio_Carrito = items_carrito.aggregate(total=Sum('producto__precio'))['total']
    except Carrito.DoesNotExist:
        # Si no existe el carrito para el usuario, inicializar variables 
        carrito = None
        items_carrito = []
        nuevo_precio_Carrito = 0
    # Actualizar el precio total del carrito si existe
    if carrito:
        carrito.total = nuevo_precio_Carrito
        carrito.save()
    # Renderizar la plantilla 'sitio/carrito/index.html' con la información necesaria
    return render(request, 'sitio/carrito/index.html', {
        'categorias': categorias,
        'usuario': usuario_logeado,
        'items_carrito': items_carrito,
        'carrito':carrito,
    })

def carrito_save(request):
    #tieneCarrito = Carrito.objects.filter(usuario=8).count()
    # Devuelve un 404 si no encuentra el carrito
    #arrito = get_object_or_404(Carrito, usuario=usuario_logeado.id)
    
    #agarramos el usuario logeado
    usuario_logeado = request.user 
    #agarramos el id del producto en especifico
    producto_id = request.POST.get('producto_id')
    #si no tiene la id procedemos a redireccionar ala index
    if not producto_id:
        return redirect("SITIO:producto_index")
    #por si tiene algun error
    producto = get_object_or_404(Producto, pk=producto_id)
    #iniciamos un try cach
    try:
        carrito = Carrito.objects.get(usuario=usuario_logeado)
    except Carrito.DoesNotExist:
        carrito = Carrito.objects.create(usuario=usuario_logeado, total=Decimal('0.00'))
     #guartdamos el item carrito y en create el producto en especifico
    item_carrito, created = Carrito_item.objects.get_or_create(carrito=carrito, producto=producto)
    #iniciamos en 0 el carrito total si no tiene nada o si no produce un error
    if carrito.total is None:
        carrito.total = Decimal('0.00')
    #procede a crear o mejor digamos lo mete en el carrito
    if created:
        carrito.total += producto.precio
        carrito.save()
        messages.success(request, f"El producto {producto.titulo} fue agregado al carrito")
    else:
        messages.warning(request, f"El producto {producto.titulo} ya está en el carrito")

    return redirect("SITIO:producto_index")

def carrito_clean(request):
    #agarramos el usuario logeado
    usuario_logeado = request.user
    #iniciamos un try cach para ver si obtiene un error y si si procedemos a sacar un 0
    try:
        carrito = Carrito.objects.get(usuario=usuario_logeado)
    except Carrito.DoesNotExist:
        carrito = Carrito.objects.create(usuario=usuario_logeado, total=0)  # Inicializar total a 0
    #limpiamos la base de datos
    carrito.items.all().delete()
    #iniciamos el contador a 0
    carrito.total = 0
    #guardamos
    carrito.save()

    return redirect('SITIO:carrito_index')

def item_carrito_delete(request, item_carrito_id):
    #agarramos un item en especifico de la base de datos
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
    
#PROCESO DE LAS NOMINAS
def nominas(request):
    datos = empleados.objects.all()
    if request.method == 'POST': 
        # Obten los datos enviados en el formulario (suponiendo que 'datos' es una lista de nombres)
         datos  = request.POST.getlist('datos')
         datos = datos[0]
        # Realiza la consulta filtrando por los nombres en la lista 'datos'
         datos = empleados.objects.filter(id=datos)
         return render(request, 'sitio/nominas/transferenciaNomina.html', {'datos': datos})
    else:
        return render(request, 'sitio/nominas/nomina.html', {'datos': datos})
        
   

def SolicitarNomina(request):
    if request.method == 'POST':
        #iniciamos el formulario
        form = TransferForm(request.POST)
    return render(request, 'sitio/nominas/TransferenciaNomina.html', {'form': form})
    
#PROCESOS DEL PRESTAMO
def Aceptarprestamo(request):
    #agarramos los elementos de prestamos
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
        #llamamos el formulario empleado
        form = EmpleadoForm(request.POST)
    return render(request, 'sitio/nominas/transferenciaPrestamo.html', {'form': form})
    
def SolicitarPrestamo(request):
    
    if request.method == 'POST':
        Monto = request.POST['Monto']
        FechaLimite = request.POST['FechaLimite']
        # Convierte la fecha a un objeto Date
        fecha_limite = datetime.strptime(FechaLimite, '%Y-%m-%d').date()
        #agarramos el usuario logeado
        nombre=request.user
        #mandamos los elementos a la base de datos prestamos        
        prestamo = prestamos(nombre=nombre,Monto=Monto,FechaLimite=fecha_limite)
        prestamo.save()  # Guarda los datos en la base de datos
        return redirect('SITIO:Prestamosolicitado')  # Redirige a la página que desees después de guardar el préstamo

    return render(request, 'sitio/prestamos/SolicitarPrestamo.html')

def Prestamosolicitado(request):
    return render(request,'sitio/prestamos/prestamoSolicitado.html')

#PROCESAR PAGO DE LA TARJETA Y DE PAYPAL

def proceso_pago(request, product_id):
    #procedemos agarrar un id determinado de la base de datos
    product = Carrito.objects.get(id=product_id)
    #agarra todo los objetos del carrito
    carrito=Carrito.objects.all()
    #procedemos con el pago de la api para futuras versiones
    if request.method == 'POST':
        form = PaymentForm(request.POST)
        """if form.is_valid():
            # Procesa el pago aquí
            # Guarda los datos en la base de datos, realiza una solicitud a una pasarela de pago, etc.
            # Redirige a una página de confirmación o realiza otras acciones
            """
    else:
       # inicializamos el payment
        form = PaymentForm()
    #procede hacer el proceso de la api paypal
    #agarramos los elementos de la base de datos de categorias
    categorias = Categoria.objects.all()
    #Elemento usuario logeado actualmente
    usuario_logeado = User.objects.get(username=request.user)
    #procedemos guardar en una varible los productos que estan en el carritos con un usuario determinado
    productos = Carrito.objects.get(usuario=usuario_logeado.id).items.all()
    #metemos en una variable carrito el objeto
    carrito = Carrito.objects.get(usuario=usuario_logeado.id)
    #inicializador
    nuevo_precio_Carrito = 0
    #Recoremos el bucle del carrito
    for item in carrito.items.all():
        nuevo_precio_Carrito += item.producto.precio
    carrito.total = nuevo_precio_Carrito
    #guardamos los elementos en el carrito
    carrito.save()
    #utilizamos el host para proceder el api paypal
    host = request.get_host()
    #imprimimos el total de la compra
    print(product.total)
    
    #Proceso Paypal Checkout

    paypal_checkout = {
        #Cuente donde ira el dinero
        'business': settings.PAYPAL_RECEIVER_EMAIL,
        #el total que se cobrara
        'amount': product.total,
       #funcion para valorar
        'invoice': uuid.uuid4(),
        #tipo de moneda
        'currency_code': 'MXN',
        #coneccion del host de paypal
        'notify_url': f"http://{host}{reverse('paypal-ipn')}",
    
    }
    #iniciacion del form del paypal
    paypal_payment = PayPalPaymentsForm(initial=paypal_checkout)
    #llevamos todo los elementos al html
    context = {
        'product': product,
        'paypal': paypal_payment,
        'categorias' : categorias,'usuario' : usuario_logeado,'items_carrito' : productos,'paypal':paypal_payment, 'carrito':carrito,'form':form,
    }

    return render(request, 'sitio/Tarjeta/TarjetaCarrito.html', context)

# VISTAS DE LOS PERFILES
#PERFIL USUARIO 
def perfil(request):
    #agarrar el usuario que esta logeado con allauth o normal
    usuario = request.user

    perfil, created = PerfilEmpleado.objects.get_or_create(user=usuario)

    if request.method == 'POST':
        form = CambiarNombreUsuarioForm(request.POST)
        if form.is_valid():
            nuevo_nombre_usuario = form.cleaned_data['nuevo_nombre_usuario']
            
            # Verificar si el nuevo nombre de usuario ya existe
            if User.objects.filter(username=nuevo_nombre_usuario).exists():
                # Manejar el caso en el que el nuevo nombre de usuario ya existe
                # Puedes mostrar un mensaje de error o redirigir a otra página
                messages.error(request, 'El nuevo nombre de usuario ya está en uso.')
            else:
                # Si no existe, cambia el nombre de usuario y guarda los cambios
                user = request.user
                user.username = nuevo_nombre_usuario
                user.save()
                
                # Redirigir a una página de éxito o a la misma página
                messages.success(request, 'Nombre de usuario actualizado exitosamente.')
                form = FotoPerfilForm(request.POST, request.FILES, instance=perfil)
                return render(request, 'sitio/perfil/empleado.html', {'usuario': usuario, 'form': form, 'perfil': perfil})
        form = FotoPerfilForm(request.POST, request.FILES, instance=perfil)
        if form.is_valid():
            # Redimensiona la imagen antes de guardarla
            img = Image.open(form.cleaned_data['foto'])
            img_resized = img.resize((200, 200))  # Ajusta el tamaño según tus necesidades
            img_resized.save(perfil.foto.path)

            form.save()

            # Redirige a la página de éxito o a la misma página
            return render(request, 'sitio/perfil/usuario.html', {'usuario': usuario, 'form': form, 'perfil': perfil})

    else:
        form = FotoPerfilForm(instance=perfil)

    return render(request, 'sitio/perfil/usuario.html', {'usuario': usuario, 'form': form, 'perfil': perfil})
    

    
# PERFIL EMPLEADO

def perfilempleado(request):
    #agarrar el usuario que esta logeado con allauth o normal
    usuario = request.user

    perfil, created = PerfilEmpleado.objects.get_or_create(user=usuario)

    if request.method == 'POST':
        form = CambiarNombreUsuarioForm(request.POST)
        if form.is_valid():
            nuevo_nombre_usuario = form.cleaned_data['nuevo_nombre_usuario']
            
            # Verificar si el nuevo nombre de usuario ya existe
            if User.objects.filter(username=nuevo_nombre_usuario).exists():
                # Manejar el caso en el que el nuevo nombre de usuario ya existe
                # Puedes mostrar un mensaje de error o redirigir a otra página
                messages.error(request, 'El nuevo nombre de usuario ya está en uso.')
            else:
                # Si no existe, cambia el nombre de usuario y guarda los cambios
                user = request.user
                user.username = nuevo_nombre_usuario
                user.save()
                
                # Redirigir a una página de éxito o a la misma página
                messages.success(request, 'Nombre de usuario actualizado exitosamente.')
                form = FotoPerfilForm(request.POST, request.FILES, instance=perfil)
                return render(request, 'sitio/perfil/empleado.html', {'usuario': usuario, 'form': form, 'perfil': perfil})
        form = FotoPerfilForm(request.POST, request.FILES, instance=perfil)
        if form.is_valid():
            # Redimensiona la imagen antes de guardarla
            img = Image.open(form.cleaned_data['foto'])
            img_resized = img.resize((200, 200))  # Ajusta el tamaño según tus necesidades
            img_resized.save(perfil.foto.path)

            form.save()

            # Redirige a la página de éxito o a la misma página
            return render(request, 'sitio/perfil/empleado.html', {'usuario': usuario, 'form': form, 'perfil': perfil})

    else:
        form = FotoPerfilForm(instance=perfil)

    return render(request, 'sitio/perfil/empleado.html', {'usuario': usuario, 'form': form, 'perfil': perfil})
 #PERFIL DEL SUPER USUARIO
def perfiladmin(request):
    #agarrar el usuario que esta logeado con allauth o normal
    usuario = request.user

    perfil, created = PerfilEmpleado.objects.get_or_create(user=usuario)

    if request.method == 'POST':
        form = CambiarNombreUsuarioForm(request.POST)
        if form.is_valid():
            nuevo_nombre_usuario = form.cleaned_data['nuevo_nombre_usuario']
            
            # Verificar si el nuevo nombre de usuario ya existe
            if User.objects.filter(username=nuevo_nombre_usuario).exists():
                # Manejar el caso en el que el nuevo nombre de usuario ya existe
                # Puedes mostrar un mensaje de error o redirigir a otra página
                messages.error(request, 'El nuevo nombre de usuario ya está en uso.')
            else:
                # Si no existe, cambia el nombre de usuario y guarda los cambios
                user = request.user
                user.username = nuevo_nombre_usuario
                user.save()
                
                # Redirigir a una página de éxito o a la misma página
                messages.success(request, 'Nombre de usuario actualizado exitosamente.')
                form = FotoPerfilForm(request.POST, request.FILES, instance=perfil)
                return render(request, 'sitio/perfil/empleado.html', {'usuario': usuario, 'form': form, 'perfil': perfil})
        form = FotoPerfilForm(request.POST, request.FILES, instance=perfil)
        if form.is_valid():
            # Redimensiona la imagen antes de guardarla
            img = Image.open(form.cleaned_data['foto'])
            img_resized = img.resize((200, 200))  # Ajusta el tamaño según tus necesidades
            img_resized.save(perfil.foto.path)

            form.save()
            # Redirige a la página de éxito o a la misma página
            return render(request, 'sitio/perfil/admin.html', {'usuario': usuario, 'form': form, 'perfil': perfil})

    else:
        form = FotoPerfilForm(instance=perfil)

    return render(request, 'sitio/perfil/admin.html', {'usuario': usuario, 'form': form, 'perfil': perfil})

  
        
        
        

    
    
    
    
    
   
    
  
    
    



