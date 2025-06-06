from config.conexion import conexion
from flask import Flask, render_template, request, redirect, session, make_response
from fpdf import FPDF

app = Flask(__name__)
app.secret_key = 'miclave'



def mostrarTodo():
    cursor = conexion.cursor()
    cursor.execute('SELECT * FROM tdclientes')
    clientes = cursor.fetchall()
    cursor.close()
    return clientes

def mostrarCliente(id):
    cursor = conexion.cursor()
    sql = 'SELECT * FROM tdclientes WHERE id_cliente=%s'
    cursor.execute(sql, (id,))
    datos = cursor.fetchone()
    cursor.close()
    return datos



@app.route('/')
def index():
    if 'usuario' in session:
        datos = mostrarTodo()
        return render_template('registrar.html', clientes=datos)
    return render_template("login.html")

@app.route('/insertar', methods=['POST'])
def insertar():
    NOMBRE = request.form['txtnombre']
    nit = request.form['txtNIT']
    cursor = conexion.cursor()
    sql = "INSERT INTO tdclientes (Nombre, nit) VALUES (%s, %s)"
    cursor.execute(sql, (NOMBRE, nit))
    conexion.commit()
    cursor.close()
    clientes = mostrarTodo()
    mensaje = "Registro insertado Exitosamente"
    return render_template('registrar.html', mensaje=mensaje, clientes=clientes)

@app.route('/actualizar/<id>')
def actualizar(id):
    cursor = conexion.cursor()
    sql = "SELECT * FROM tdclientes WHERE id_cliente=%s"
    cursor.execute(sql, (id,))
    dato = cursor.fetchone()
    cursor.close()
    return render_template('actualizar.html', dato=dato)

@app.route('/actualizar_cliente', methods=['POST'])
def actualizar_cliente():
    id = request.form['txtid']
    nombre = request.form['txtnombre']
    nit = request.form['txtNIT']
    cursor = conexion.cursor()
    sql = "UPDATE tdclientes SET nombre=%s, nit=%s WHERE id_cliente=%s"
    cursor.execute(sql, (nombre, nit, id))
    conexion.commit()
    cursor.close()
    return redirect('/')

@app.route('/eliminar/<id>')
def eliminar(id):
    cursor = conexion.cursor()
    sql = "DELETE FROM tdclientes WHERE id_cliente=%s"
    cursor.execute(sql, (id,))
    conexion.commit()
    cursor.close()
    return redirect('/')

@app.route('/comprar/<id>')
def comprar(id):
    datos = mostrarCliente(id)
    return render_template('comprar.html', id=id, datos=datos)

@app.route('/comprar', methods=['POST'])
def insertarComprar():
    id = request.form['txtid']
    producto = request.form['txtproducto']
    cantidad = request.form['txtcantidad']
    costo = request.form['txtcosto']
    cursor = conexion.cursor()
    sql = "INSERT INTO tdcompra (producto, cantidad, costo, tdClientes_id_cliente) VALUES (%s, %s, %s, %s)"
    cursor.execute(sql, (producto, cantidad, costo, id))
    conexion.commit()
    cursor.close()
    return redirect('/')

@app.route('/vercompras/<id>', methods=['GET'])
def vercompras(id):
    cursor = conexion.cursor()
    sql = "SELECT * FROM tdcompra WHERE tdClientes_id_cliente=%s"
    cursor.execute(sql, (id,))
    datos = cursor.fetchall()
    cursor.close()
    return render_template('vercompras.html', datos=datos)

@app.route('/buscar', methods=['GET'])
def buscar():
    buscar = request.args.get('txtbuscar')
    cursor = conexion.cursor()
    sql = "SELECT * FROM tdclientes WHERE nombre LIKE %s"
    cursor.execute(sql, (buscar + '%',))
    datos = cursor.fetchall()
    cursor.close()
    return render_template('registrar.html', clientes=datos)

@app.route('/reporte/<id>')
def generar_pdf(id):
    cursor = conexion.cursor()
    sql = """
    SELECT c.nombre, c.nit, co.producto, co.cantidad, co.costo
    FROM tdcompra co
    INNER JOIN tdclientes c ON co.tdClientes_id_cliente = c.id_cliente
    WHERE co.tdClientes_id_cliente = %s
    """
    cursor.execute(sql, (id,))
    datos = cursor.fetchall()
    cursor.close()

    if not datos:
        return "No se encontraron compras para este cliente", 404

    nombre_cliente = datos[0][0]
    nit_cliente = datos[0][1]

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="REPORTE DE COMPRAS", ln=True, align="C")
    pdf.ln(10)
    pdf.cell(200, 10, txt=f"Cliente: {nombre_cliente}", ln=True)
    pdf.cell(200, 5, txt=f"NIT: {nit_cliente}", ln=True)
    pdf.ln(5)

    pdf.set_font("Arial", 'B', 10)
    pdf.cell(60, 10, "Producto", 1)
    pdf.cell(30, 10, "Cantidad", 1)
    pdf.cell(30, 10, "Costo", 1)
    pdf.cell(40, 10, "Total", 1)
    pdf.ln()

    pdf.set_font("Arial", '', 10)
    for fila in datos:
        _, _, producto, cantidad, costo = fila
        total = float(cantidad) * float(costo)
        pdf.cell(60, 10, str(producto), 1)
        pdf.cell(30, 10, str(cantidad), 1)
        pdf.cell(30, 10, f"{costo:.2f}", 1)
        pdf.cell(40, 10, f"{total:.2f}", 1)
        pdf.ln()

    response = make_response(pdf.output(dest='S').encode('latin1'))
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'inline; filename=reporte_compras.pdf'
    return response

@app.route('/login', methods=['GET', 'POST'])
def login():
    mensaje = ''
    if request.method == 'POST':
        user = request.form['txtuser']
        clave = request.form['txtclave']
        cursor = conexion.cursor()
        sql = 'SELECT * FROM tbusuario WHERE user=%s AND clave=%s'
        cursor.execute(sql, (user, clave))
        usuario = cursor.fetchone()
        cursor.close()

        if usuario:
            session['usuario'] = usuario[1]
            session['clave'] = usuario[3]
            return redirect('/')
        else:
            mensaje = "Usuario o contraseña incorrecto"
    return render_template('login.html', mensaje=mensaje)

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')


if __name__ == '__main__':
    app.run(debug=True)
    