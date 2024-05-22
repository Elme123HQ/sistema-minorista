import tkinter as tk
from tkinter import ttk
import sqlite3
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors

# Función para conectar con la base de datos
def conectar_bd():
    conexion = sqlite3.connect('punto_venta.db')
    cursor = conexion.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS productos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            precio REAL NOT NULL,
            cantidad INTEGER NOT NULL
        )
    ''')
    conexion.commit()
    return conexion, cursor

# Función para cerrar la conexión con la base de datos
def cerrar_bd(conexion):
    conexion.close()

# Función para insertar un producto en la base de datos
def insertar_producto(nombre, precio, cantidad=1):
    conexion, cursor = conectar_bd()
    cursor.execute('INSERT INTO productos (nombre, precio, cantidad) VALUES (?, ?, ?)', (nombre, precio, cantidad))
    conexion.commit()
    cerrar_bd(conexion)

# Función para agregar un producto a la base de datos
def agregar_producto():
    nombre = nombre_producto.get()
    precio = precio_producto.get()
    cantidad = cantidad_producto.get()
    if nombre and precio and cantidad:
        try:
            precio = float(precio)
            cantidad = int(cantidad)
            if precio > 0 and cantidad > 0:
                insertar_producto(nombre, precio, cantidad)
                cargar_productos()  # Actualizar la lista de productos después de agregar uno nuevo
                # Limpiar los campos después de agregar el producto
                nombre_producto.delete(0, tk.END)
                precio_producto.delete(0, tk.END)
                cantidad_producto.delete(0, tk.END)
                actualizar_productos_disponibles()  # Actualizar el Combobox de productos disponibles
            else:
                print("El precio y la cantidad deben ser números positivos.")
        except ValueError:
            print("El precio y la cantidad deben ser números válidos.")
    else:
        print("Por favor, complete todos los campos.")

# Función para cargar los productos desde la base de datos y mostrarlos en la tabla
def cargar_productos():
    conexion, cursor = conectar_bd()
    cursor.execute('SELECT * FROM productos')
    productos = cursor.fetchall()
    tabla_inventario.delete(*tabla_inventario.get_children()) # Limpiar la tabla antes de cargar los productos
    for producto in productos:
        tabla_inventario.insert('', 'end', values=producto)
    cerrar_bd(conexion)

# Función para eliminar un producto de la base de datos
def eliminar_producto():
    seleccion = tabla_inventario.selection()
    if seleccion:
        id_producto = tabla_inventario.item(seleccion, 'values')[0]
        conexion, cursor = conectar_bd()
        cursor.execute('DELETE FROM productos WHERE id = ?', (id_producto,))
        conexion.commit()
        cargar_productos()  # Actualizar la lista de productos después de eliminar uno
        cerrar_bd(conexion)
        actualizar_productos_disponibles()  # Actualizar el Combobox de productos disponibles

# Función para actualizar la lista de productos en el Combobox
def actualizar_productos_disponibles():
    conexion, cursor = conectar_bd()
    cursor.execute('SELECT nombre FROM productos')
    productos = cursor.fetchall()
    productos_disponibles['values'] = [producto[0] for producto in productos]
    cerrar_bd(conexion)

# Función para buscar productos en tiempo real
def buscar_productos(event=None):
    valor = nombre_producto.get()
    conexion, cursor = conectar_bd()
    cursor.execute('SELECT * FROM productos WHERE nombre LIKE ?', ('%' + valor + '%',))
    productos = cursor.fetchall()
    tabla_inventario.delete(*tabla_inventario.get_children())
    for producto in productos:
        tabla_inventario.insert('', 'end', values=producto)
    cerrar_bd(conexion)

# Función para generar e imprimir la boleta en PDF
def generar_e_imprimir_boleta():
    nombre_cliente = nombre_cliente_boleta.get()
    productos = []
    for item in tabla_boleta.get_children():
        producto = tabla_boleta.item(item, 'values')
        productos.append(producto)
    if nombre_cliente and productos:
        if not nombre_cliente.isdigit():  # Validar que el nombre del cliente no sea un número
            total = generar_factura(productos, nombre_cliente)
            print(f"Boleta generada e impresa para: {nombre_cliente}")
            print(f"Total de la compra: ${total:.2f}")
        else:
            print("El nombre del cliente no puede ser un número.")
    else:
        print("Por favor, ingrese el nombre del cliente y seleccione al menos un producto.")

# Función para generar el PDF de la factura
def generar_factura(productos, nombre_cliente):
    pdf_filename = f'factura_{nombre_cliente}.pdf'
    doc = SimpleDocTemplate(pdf_filename, pagesize=letter)

    # Detalles de la compra
    data = [['ID', 'Producto', 'Precio', 'Cantidad', 'Subtotal']]
    total = 0
    for producto in productos:
        if len(producto) == 4:  # Verificar si hay suficientes valores en el producto
            id_producto, nombre, precio, cantidad = producto
            precio = float(precio)  # Convertir a flotante sin el símbolo de dólar
            subtotal = precio * float(cantidad)
            total += subtotal
            data.append([id_producto, nombre, precio, cantidad, f"${subtotal:.2f}"])
    data.append(['', '', '', 'Total:', f"${total:.2f}"])

    # Estilo de la tabla
    style = TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                                                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                        ('BACKGROUND', (0, 1), (-1, -2), colors.beige),
                        ('GRID', (0, 0), (-1, -1), 1, colors.black)])

    # Crear tabla
    tabla = Table(data)

    # Aplicar estilo a la tabla
    tabla.setStyle(style)

    # Construir la página
    contenido = [tabla]
    doc.build(contenido)

    return total

# Crear la ventana principal
ventana = tk.Tk()
ventana.title("Sistema de Punto de Venta")

# Crear el contenedor de pestañas
pestanas = ttk.Notebook(ventana)

# Pestaña para agregar productos
pestana_agregar = ttk.Frame(pestanas)
pestanas.add(pestana_agregar, text='Agregar Productos')

# Etiquetas y campos de entrada para el nombre, precio y cantidad del producto
tk.Label(pestana_agregar, text="Nombre del Producto:").grid(row=0, column=0, padx=5, pady=5)
nombre_producto = tk.Entry(pestana_agregar)
nombre_producto.grid(row=0, column=1, padx=5, pady=5)
nombre_producto.bind('<KeyRelease>', buscar_productos)  # Llama a buscar_productos en tiempo real

tk.Label(pestana_agregar, text="Precio del Producto:").grid(row=1, column=0, padx=5, pady=5)
precio_producto = tk.Entry(pestana_agregar)
precio_producto.grid(row=1, column=1, padx=5, pady=5)
tk.Label(pestana_agregar, text="Cantidad:").grid(row=2, column=0, padx=5, pady=5)  # Etiqueta para la cantidad
cantidad_producto = tk.Entry(pestana_agregar)
cantidad_producto.grid(row=2, column=1, padx=5, pady=5)  # Campo de entrada para la cantidad

# Botón para agregar productos a la base de datos
boton_agregar_producto = tk.Button(pestana_agregar, text="Agregar Producto", command=agregar_producto)
boton_agregar_producto.grid(row=3, column=0, columnspan=2, padx=5, pady=5)

# Botón para eliminar un producto de la base de datos
boton_eliminar_producto = tk.Button(pestana_agregar, text="Eliminar Producto", command=eliminar_producto)
boton_eliminar_producto.grid(row=4, column=0, columnspan=2, padx=5, pady=5)

# Botón para actualizar la lista de productos en la tabla
boton_actualizar_productos = tk.Button(pestana_agregar, text="Actualizar", command=cargar_productos)
boton_actualizar_productos.grid(row=5, column=0, columnspan=2, padx=5, pady=5)

# Tabla para mostrar los productos en la pestaña de agregar productos
tabla_inventario = ttk.Treeview(pestana_agregar, columns=("ID", "Nombre", "Precio", "Cantidad"))
tabla_inventario.grid(row=6, column=0, columnspan=2, padx=5, pady=5)
tabla_inventario.heading("#0", text="ID")
tabla_inventario.heading("#1", text="Nombre")
tabla_inventario.heading("#2", text="Precio")
tabla_inventario.heading("#3", text="Cantidad")

# Pestaña para generar boletas
pestana_boletas = ttk.Frame(pestanas)
pestanas.add(pestana_boletas, text='Generar Boletas')

# Etiqueta y campo de entrada para el nombre del cliente
tk.Label(pestana_boletas, text="Nombre del Cliente:").grid(row=0, column=0, padx=5, pady=5)
nombre_cliente_boleta = tk.Entry(pestana_boletas)
nombre_cliente_boleta.grid(row=0, column=1, padx=5, pady=5)

# Botón para agregar productos a la boleta
def agregar_producto_boleta():
    producto_seleccionado = productos_disponibles.get()
    cantidad = cantidad_producto_boleta.get()
    if producto_seleccionado and cantidad:
        try:
            cantidad = int(cantidad)
            if cantidad > 0:
                conexion, cursor = conectar_bd()
                cursor.execute('SELECT precio FROM productos WHERE nombre = ?', (producto_seleccionado,))
                precio = cursor.fetchone()[0]
                cerrar_bd(conexion)
                subtotal = float(precio) * cantidad  # Calcular el subtotal como un número flotante
                tabla_boleta.insert('', 'end', values=(producto_seleccionado, cantidad, precio, subtotal))  # Insertar el subtotal como número flotante
                cantidad_producto_boleta.delete(0, tk.END)
            else:
                print("La cantidad debe ser un número positivo.")
        except ValueError:
            print("La cantidad debe ser un número válido.")


boton_agregar_producto_boleta = tk.Button(pestana_boletas, text="Agregar Producto", command=agregar_producto_boleta)
boton_agregar_producto_boleta.grid(row=1, column=0, padx=5, pady=5)

# Combobox para seleccionar productos
productos_disponibles = ttk.Combobox(pestana_boletas)  # Se creará vacío inicialmente
productos_disponibles.grid(row=1, column=1, padx=5, pady=5)

# Campo de entrada para la cantidad de productos
cantidad_producto_boleta = tk.Entry(pestana_boletas)
cantidad_producto_boleta.grid(row=1, column=2, padx=5, pady=5)

# Etiqueta y tabla para mostrar los productos agregados a la boleta
tk.Label(pestana_boletas, text="Productos en la Boleta:").grid(row=2, column=0, padx=5, pady=5, columnspan=3)
tabla_boleta = ttk.Treeview(pestana_boletas, columns=("Producto", "Cantidad", "Precio", "Subtotal"))
tabla_boleta.grid(row=3, column=0, columnspan=3, padx=5, pady=5)
tabla_boleta.heading("#0", text="Producto")
tabla_boleta.heading("#1", text="Cantidad")
tabla_boleta.heading("#2", text="Precio")
tabla_boleta.heading("#3", text="Subtotal")

# Botón para eliminar un producto de la boleta
def eliminar_producto_boleta():
    seleccion = tabla_boleta.selection()
    if seleccion:
        tabla_boleta.delete(seleccion)

boton_eliminar_producto_boleta = tk.Button(pestana_boletas, text="Eliminar Producto", command=eliminar_producto_boleta)
boton_eliminar_producto_boleta.grid(row=4, column=0, padx=5, pady=5)

# Botón para generar e imprimir la boleta
boton_generar_boleta = tk.Button(pestana_boletas, text="Generar e Imprimir Boleta", command=generar_e_imprimir_boleta)
boton_generar_boleta.grid(row=4, column=1, columnspan=2, padx=5, pady=5)

# Actualizar productos disponibles al inicio
actualizar_productos_disponibles()

# Enlazar la acción de presionar Enter en el campo de cantidad_producto_boleta con agregar_producto_boleta
cantidad_producto_boleta.bind('<Return>', lambda event=None: agregar_producto_boleta())

# Configurar el tamaño y la posición de la ventana
ventana.geometry("1013x460")

# Añadir el contenedor de pestañas a la ventana principal
pestanas.pack(expand=True, fill='both')

# Ejecutar el bucle de la aplicación
ventana.mainloop()
