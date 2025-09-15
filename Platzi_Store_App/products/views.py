import requests
import json
from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required

# URL base de la API de Platzi Fake Store
API_URL = "https://api.escuelajs.co/api/v1/products/"
CATEGORIES_API_URL = "https://api.escuelajs.co/api/v1/categories/"

def home(request):
    """
    Renderiza la página de inicio.
    """
    return render(request, 'home.html')

def product_list(request):
    """
    Muestra una lista de productos.
    Permite filtrar por categoría o buscar por nombre de producto.
    """
    product_name_query = request.GET.get('product_name')
    category_id_query = request.GET.get('category_id')
    
    # Fetch all categories for the dropdown
    categories = []
    try:
        cat_response = requests.get(CATEGORIES_API_URL)
        cat_response.raise_for_status()
        # Filter out categories without a name or with a generic image
        categories = [cat for cat in cat_response.json() if cat.get('name') and 'https://via.placeholder.com' not in cat.get('image', '')]
    except requests.RequestException as e:
        messages.error(request, f"Error al obtener las categorías: {e}")

    products = []
    try:
        # If a product name is searched
        if product_name_query:
            response = requests.get(f"{API_URL}?title={product_name_query}")
            response.raise_for_status()
            products = response.json()
            if not products:
                messages.warning(request, f"No se encontraron productos con el nombre: '{product_name_query}'.")
            else:
                messages.success(request, f"Mostrando resultados para: '{product_name_query}'.")
        # If a category is selected, filter products
        elif category_id_query and category_id_query.isdigit():
            category_id = int(category_id_query)
            response = requests.get(f"{CATEGORIES_API_URL}{category_id}/products")
            response.raise_for_status()
            products = response.json()
            if not products:
                messages.warning(request, f"No se encontraron productos para la categoría seleccionada.")
            else:
                # Find category name for the message
                category_name = next((cat['name'] for cat in categories if cat['id'] == category_id), f"ID: {category_id}")
                messages.success(request, f"Mostrando productos de la categoría: {category_name}.")
        # Otherwise, show the general list
        else:
            response = requests.get(f"{API_URL}?offset=0&limit=20")
            response.raise_for_status()
            products = response.json()

    except requests.RequestException as e:
        messages.error(request, f"Error al comunicar con la API: {e}")
        products = []

    # Filter products that don't have the expected structure and add category info if missing
    valid_products = []
    for p in products:
        if 'category' not in p and category_id_query:
            p['category'] = {'id': category_id_query}
            
        if p.get('images') and isinstance(p.get('images'), list) and len(p['images']) > 0 and p.get('price', 0) > 0 and p.get('category'):
            if isinstance(p['images'][0], str) and p['images'][0].startswith('http'):
                 valid_products.append(p)
    
    search_values = {
        'product_name': product_name_query,
        'category_id': category_id_query
    }

    return render(request, 'product_list.html', {
        'products': valid_products, 
        'search_values': search_values,
        'categories': categories
    })

@login_required
def create_product(request):
    """
    Maneja la creación de un nuevo producto y redirige a su página de detalle.
    """
    if request.method == 'POST':
        title = request.POST.get('title')
        price = request.POST.get('price')
        description = request.POST.get('description')
        category_id = request.POST.get('categoryId')
        image_url = request.POST.get('image')

        if not all([title, price, description, category_id, image_url]):
            messages.error(request, "Todos los campos son obligatorios.")
            return render(request, 'create.html', {'form_data': request.POST})

        try:
            payload = {
                "title": title,
                "price": int(price),
                "description": description,
                "categoryId": int(category_id),
                "images": [image_url]
            }
            response = requests.post(API_URL, json=payload)
            response.raise_for_status()
            new_product = response.json()
            if response.status_code == 201 and 'id' in new_product:
                 messages.success(request, f"¡Producto '{new_product.get('title')}' creado con éxito!")
                 return redirect('product_detail', product_id=new_product['id'])
            else:
                error_message = new_product.get('message', 'Ocurrió un error desconocido en la API.')
                messages.error(request, f"Error de la API: {error_message}")
        except (requests.RequestException, ValueError) as e:
            messages.error(request, f"Error al crear el producto: {e}")
        return render(request, 'create.html', {'form_data': request.POST})
    return render(request, 'create.html')

def product_detail(request, product_id):
    """
    Muestra el detalle de un producto específico obtenido de la API.
    """
    try:
        response = requests.get(f"{API_URL}{product_id}")
        response.raise_for_status()
        product = response.json()
        if not (product.get('images') and isinstance(product.get('images'), list) and len(product['images']) > 0):
            product['images'] = ['https://via.placeholder.com/640x480.png?text=No+Image']
        if not (product.get('category') and isinstance(product.get('category'), dict)):
            product['category'] = {'name': 'Sin categoría', 'id': 'N/A'}
    except requests.RequestException:
        messages.error(request, "El producto solicitado no existe o no se pudo encontrar.")
        return redirect('products_list')
    return render(request, 'product_detail.html', {'product': product})

@login_required
def update_product(request, product_id):
    """
    Maneja la actualización de un producto existente.
    """
    product_url = f"{API_URL}{product_id}"

    if request.method == 'POST':
        title = request.POST.get('title')
        price = request.POST.get('price')
        description = request.POST.get('description')
        image_url = request.POST.get('image')

        if not all([title, price, description, image_url]):
            messages.error(request, "Todos los campos son obligatorios.")
            try:
                response = requests.get(product_url)
                response.raise_for_status()
                product = response.json()
            except requests.RequestException:
                messages.error(request, "No se pudo recuperar el producto para editar.")
                return redirect('products_list')
            return render(request, 'update_product.html', {'product': product})

        try:
            payload = { "title": title, "price": int(price), "description": description, "images": [image_url] }
            response = requests.put(product_url, json=payload)
            response.raise_for_status()
            updated_product = response.json()
            messages.success(request, f"Producto '{updated_product.get('title')}' actualizado con éxito.")
            return redirect('product_detail', product_id=updated_product['id'])
        except (requests.RequestException, ValueError) as e:
            messages.error(request, f"Error al actualizar el producto: {e}")
            submitted_data = {'id': product_id, 'title': title, 'price': price, 'description': description, 'images': [image_url]}
            return render(request, 'update_product.html', {'product': submitted_data})
    else: # GET request
        try:
            response = requests.get(product_url)
            response.raise_for_status()
            product = response.json()
            
            if isinstance(product.get('images'), str):
                try:
                    product['images'] = json.loads(product['images'])
                except json.JSONDecodeError:
                    product['images'] = json.loads(product['images'].replace("'", '"'))
            
            if not (product.get('images') and isinstance(product.get('images'), list) and len(product['images']) > 0):
                 product['images'] = ['']
        except requests.RequestException:
            messages.error(request, "El producto que intentas editar no existe.")
            return redirect('products_list')
        
        return render(request, 'update_product.html', {'product': product})

@login_required
@require_POST
def delete_product(request, product_id):    
    """
    Elimina un producto de la tienda.
    """
    try:
        response = requests.delete(f"{API_URL}{product_id}")
        response.raise_for_status()
        
        if response.json() is True:
            messages.success(request, "Producto eliminado con éxito.")
        else:
            messages.error(request, "La API no confirmó la eliminación del producto.")
    except requests.RequestException as e:
        messages.error(request, f"Error al eliminar el producto: {e}")

    return redirect('products_list')