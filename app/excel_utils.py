from openpyxl import load_workbook
from app.models import Tramitacion
import os
from datetime import datetime


def generar_excel(tramitacion: Tramitacion) -> str:
    plantilla_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Plantilla.xlsx")
    wb = load_workbook(plantilla_path)
    sheet = wb.worksheets[0]

    # Si hay productos, usar el primero para los datos generales
    if tramitacion.productos:
        primer_producto = tramitacion.productos[0]
        sheet["C4"] = primer_producto.num_albaran
        sheet["C5"] = primer_producto.num_tramitacion
        sheet["C6"] = primer_producto.fecha.strftime("%Y-%m-%d")

    # Escribir productos a partir de la fila 9
    fila = 9
    for producto in tramitacion.productos:
        sheet[f"B{fila}"] = producto.modelo
        sheet[f"C{fila}"] = producto.sn_imei
        sheet[f"D{fila}"] = producto.descripcion_averia
        sheet[f"E{fila}"] = producto.caja
        sheet[f"F{fila}"] = producto.cargador
        sheet[f"G{fila}"] = producto.otros
        sheet[f"H{fila}"] = producto.parte
        sheet[f"I{fila}"] = producto.de_tienda
        sheet[f"J{fila}"] = producto.codigo_interno
        fila += 1

    # Guardar solo en la carpeta local 'archivos_generados'
    now = datetime.now()
    carpeta = "archivos_generados"
    os.makedirs(carpeta, exist_ok=True)
    nombre_archivo = f"tramitacion_{tramitacion.id}_{now.strftime('%Y%m%d')}.xlsx"
    ruta_archivo = os.path.join(carpeta, nombre_archivo)
    wb.save(ruta_archivo)

    # Crear carpeta con el número de tramitación (del primer producto)
    if tramitacion.productos:
        num_tramitacion = tramitacion.productos[0].num_tramitacion.replace('/', '_')
        carpeta_tramitacion = os.path.join(carpeta, num_tramitacion)
        os.makedirs(carpeta_tramitacion, exist_ok=True)
        # Mover el Excel
        ruta_excel_final = os.path.join(carpeta_tramitacion, nombre_archivo)
        os.replace(ruta_archivo, ruta_excel_final)
        # Buscar y mover el PDF del albarán
        num_albaran = tramitacion.productos[0].num_albaran
        patron_pdf = os.path.join(carpeta, f"albaran_{num_albaran}.pdf")
        if os.path.exists(patron_pdf):
            os.replace(patron_pdf, os.path.join(carpeta_tramitacion, f"albaran_{num_albaran}.pdf"))
        return ruta_excel_final
    return ruta_archivo