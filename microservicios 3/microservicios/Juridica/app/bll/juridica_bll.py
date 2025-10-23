from app.dal.juridica_dal import obtener_automatizaciones, obtener_automatizacion_por_id, obtener_CC_aConsultar, obtener_CC_aConsultarRunt, obtener_automatizacion_por_idRunt
from app.dal.juridica_dal import obtener_automatizaciones, obtener_automatizacionesRunt, obtener_automatizacion_por_idRues, obtener_automatizacionesRues, obtener_CC_aConsultarRues
from app.dal.juridica_dal import obtener_automatizacionesSimit, obtener_automatizacion_por_idSimit, obtener_CC_aConsultarSimit
from app.dal.juridica_dal import obtener_automatizacionesVigilancia, obtener_automatizacion_por_idVigilancia, obtener_Radicado_aConsultarVigilancia
from app.dal.juridica_dal import obtener_automatizacionesCamaraComercio, obtener_automatizacion_por_idCamaraComercio, obtener_CC_aConsultarCamaraComercio
from app.dal.juridica_dal import obtener_automatizacion_por_idJuridico, obtener_automatizacionesJuridico, EncabezadoModel, insertar_encabezado, insertar_detalle, correo_ya_enviado, obtener_correo_usuarioJuridico, obtener_idUsuario_por_encabezado, marcar_correo_enviado, marcar_pausa_encabezado, pausar_detalle_encabezado, quitar_pausa_encabezado, reanudar_detalle_encabezado
from app.dal.juridica_dal import obtener_automatizacionesTyba, obtener_automatizacion_por_idTyba, obtener_CC_aConsultarTyba
from app.dal.juridica_dal import obtener_automatizacionesVigencia, obtener_automatizacion_por_idVigencia, insertar_encabezadoVigencia, insertar_detalleVigencia, obtener_correo_usuarioVigencia, correo_ya_enviadoVigencia, obtener_idUsuario_por_encabezadoVigencia, marcar_correo_enviadoVigencia, marcar_pausa_encabezadoVigencia, pausar_detalle_encabezadoVigencia, quitar_pausa_encabezadoVigencia, reanudar_detalle_encabezadoVigencia
from app.dal.juridica_dal import contar_detalles_por_encabezadoSuperNotariado, obtener_detalles_por_encabezado_paginadoSuperNotariado, contar_total_por_encabezadoSuperNotariado, contar_procesados_por_encabezadoSuperNotariado, obtener_encabezados_paginado_SuperNotariado, contar_encabezados_SuperNotariado
from app.dal.juridica_dal import contar_detalles_por_encabezadoRunt, obtener_detalles_por_encabezado_paginadoRunt,  contar_total_por_encabezadoRunt, contar_procesados_por_encabezadoRunt, obtener_encabezados_paginado_Runt, contar_encabezados_Runt
from app.dal.juridica_dal import contar_detalles_por_encabezadoRues, obtener_detalles_por_encabezado_paginadoRues, contar_total_por_encabezadoRues, contar_procesados_por_encabezadoRues, obtener_encabezados_paginado_Rues, contar_encabezados_Rues 
from app.dal.juridica_dal import contar_detalles_por_encabezadoSimit, obtener_detalles_por_encabezado_paginadoSimit, contar_total_por_encabezadoSimit, contar_procesados_por_encabezadoSimit, obtener_encabezados_paginado_Simit, contar_encabezados_Simit
from app.dal.juridica_dal import contar_detalles_por_encabezadoVigilancia, obtener_detalles_por_encabezado_paginadoVigilancia, contar_total_por_encabezadoVigilancia, contar_procesados_por_encabezadoVigilancia, obtener_encabezados_paginado_Vigilancia, contar_encabezados_Vigilancia
from app.dal.juridica_dal import contar_detalles_por_encabezadoCamaraComercio, obtener_detalles_por_encabezado_paginadoCamaraComercio, contar_total_por_encabezadoCamaraComercio, contar_procesados_por_encabezadoCamaraComercio, obtener_encabezados_paginado_CamaraComercio, contar_encabezados_CamaraComercio
from app.dal.juridica_dal import contar_detalles_por_encabezadoTyba, obtener_detalles_por_encabezado_paginadoTyba, contar_total_por_encabezadoTyba, contar_procesados_por_encabezadoTyba, obtener_encabezados_paginado_Tyba, contar_encabezados_Tyba
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.config.email_config import REMITENTE, PASSWORD, SERVER, PORT

#----------- SUPERNOTARIADO-------------------------------------------
def listar_automatizaciones_estado():
    """
    Lista todas las automatizaciones del módulo jurídico, con cálculo de estado y porcentaje de progreso.

    Detalles:
    - Llama a la función DAL `obtener_automatizaciones()` para traer datos de la base.
    - Si hay error (rows es None), lanza excepción para controlar fallo en la capa de datos.
    - Para cada fila válida:
      - Calcula porcentaje de detalles ingresados respecto al total.
      - Define estado:
        * "No iniciada" si no hay detalles ingresados.
        * "Finalizada" si detalles ingresados >= total.
        * "En progreso (x%)" con porcentaje calculado en caso intermedio.
    - Devuelve lista de diccionarios con id, nombre, fecha, totales y estado, lista para consumo.
    """

    rows, error = obtener_automatizaciones()
    
    if rows is None:
        raise Exception(f"Error al obtener automatizaciones: {error}")

    resultados = []
    for row in rows:
        if not row or row.totalRegistros is None or row.detallesIngresados is None:
            continue

        if row.estado and row.estado == "Pausado":
            estado = "Pausado"
        else:
            porcentaje = (row.detallesIngresados / row.totalRegistros) * 100 if row.totalRegistros else 0
            estado = (
                "No iniciada" if row.detallesIngresados == 0 else
                "Finalizada" if row.detallesIngresados >= row.totalRegistros else
                f"En progreso ({int(porcentaje)}%)"
        )

        resultados.append({
            "idEncabezado": row.idEncabezado,
            "automatizacion": row.automatizacion,
            "fechaCargue": str(row.fechaCargue),
            "totalRegistros": row.totalRegistros,
            "detallesIngresados": row.detallesIngresados,
            "estado": estado,
            "nombreUsuario": getattr(row, "nombreUsuario", "Desconocido")
        })

    return resultados


def obtener_automatizacion(id_encabezado: int):
    """
    Obtiene una automatización completa con sus detalles asociados por ID.

    Detalles:
    - Llama a DAL `obtener_automatizacion_por_id()` para traer datos.
    - Si no hay registros, lanza excepción de error.
    - Construye un diccionario `encabezado` con datos principales.
    - Llena la lista `detalles` con registros de detalle si existen.
    - Devuelve diccionario estructurado con encabezado y detalles para uso en API.
    """

    rows, error = obtener_automatizacion_por_id(id_encabezado)
    if not rows:
        raise Exception(f"Error al obtener automatización: {error}")

    encabezado = {
        "idEncabezado": rows[0].idEncabezado,
        "automatizacion": rows[0].automatizacion,
        "fechaCargue": str(rows[0].fechaCargue),
        "totalRegistros": rows[0].totalRegistros,
        "detalles": []
    }

    for row in rows:
        if row.idDetalle is not None:
            encabezado["detalles"].append({
                "idDetalle": row.idDetalle,
                "CC": row.CC,
                "numItem": row.numItem,
                "ciudad": row.ciudad,
                "matricula": row.matricula,
                "direccion": row.direccion,
                "vinculadoA": row.vinculadoA
            })

    return encabezado


def obtener_automatizacionCC():
    """
    Retorna la siguiente tupla (idEncabezado, cedula) pendiente.
    Lanza excepción si hay un error, o devuelve None si no hay más cédulas.
    """
    filas, error = obtener_CC_aConsultar()
    if error:
        raise Exception(f"Error al consultar próxima cédula: {error}")
    if not filas:
        return None
    return filas[0]

def listar_detalles_por_encabezado_paginadoBLLSuperNotariado(id_encabezado: int, offset: int = 0, limit: int = 50, CC: str | None = None):
    total = contar_detalles_por_encabezadoSuperNotariado(id_encabezado, CC)
    rows = obtener_detalles_por_encabezado_paginadoSuperNotariado(id_encabezado, offset, limit, CC)
    return {"rows": rows, "total": total}

def resumen_encabezadoBLLSuperNotariado(id_encabezado: int):
    total = contar_total_por_encabezadoSuperNotariado(id_encabezado)
    procesados = contar_procesados_por_encabezadoSuperNotariado(id_encabezado)
    return {"idEncabezado": id_encabezado, "totalRegistros": total, "procesados": procesados}

def listar_encabezados_paginado_SuperNotariado_bll(offset: int, limit: int):
    rows = obtener_encabezados_paginado_SuperNotariado(offset, limit)
    if rows is None:
        raise Exception("Error al obtener encabezados paginados")

    resultados = []
    for row in rows:
        if not row:
            continue
        total = getattr(row, "totalRegistros", 0) or 0
        ingresados = getattr(row, "detallesIngresados", 0) or 0
        if getattr(row, "estado", None) == "Pausado":
            estado = "Pausado"
        else:
            porcentaje = (ingresados / total * 100) if total else 0
            estado = (
                "No iniciada" if ingresados == 0 else
                "Finalizada" if ingresados >= total else
                f"En progreso ({int(porcentaje)}%)"
            )

        resultados.append({
            "idEncabezado": row.idEncabezado,
            "automatizacion": row.automatizacion,
            "fechaCargue": str(row.fechaCargue),
            "totalRegistros": total,
            "detallesIngresados": ingresados,
            "estado": estado,
            "nombreUsuario": getattr(row, "nombreUsuario", "Desconocido")
        })

    total_enc = contar_encabezados_SuperNotariado()
    return {"rows": resultados, "total": total_enc}

#-------------- RUNT--------------
def listar_automatizaciones_estadoRunt():
    """
    Lista todas las automatizaciones para el módulo Runt, con cálculo de estado y progreso.

    Detalles:
    - Similar a `listar_automatizaciones_estado()`, pero para Runt.
    - Usa DAL `obtener_automatizacionesRunt()`.
    - Maneja errores y construye estado con porcentaje.
    """
    rows, error = obtener_automatizacionesRunt()
    
    if rows is None:
        raise Exception(f"Error al obtener automatizaciones: {error}")

    resultados = []
    for row in rows:
        if not row or row.totalRegistros is None or row.detallesIngresados is None:
            continue

        if row.estado and row.estado == "Pausado":
            estado = "Pausado"
        else:
            porcentaje = (row.detallesIngresados / row.totalRegistros) * 100 if row.totalRegistros else 0
            estado = (
                "No iniciada" if row.detallesIngresados == 0 else
                "Finalizada" if row.detallesIngresados >= row.totalRegistros else
                f"En progreso ({int(porcentaje)}%)"
        )

        resultados.append({
            "idEncabezado": row.idEncabezado,
            "automatizacion": row.automatizacion,
            "fechaCargue": str(row.fechaCargue),
            "totalRegistros": row.totalRegistros,
            "detallesIngresados": row.detallesIngresados,
            "estado": estado,
            "nombreUsuario": getattr(row, "nombreUsuario", "Desconocido")
        })

    return resultados


def obtener_automatizacionRunt(id_encabezado: int):
    """
    Obtiene una automatización Runt completa con detalles por ID.

    Detalles:
    - Llama a DAL `obtener_automatizacion_por_idRunt()`.
    - Si no hay registros, retorna None.
    - Construye diccionario con encabezado y lista de detalles con campos específicos para Runt.
    - Devuelve la estructura lista para consumo en API.
    """
    rows = obtener_automatizacion_por_idRunt(id_encabezado)
    if not rows:
        return None

    encabezado = {
        "idEncabezado": rows[0].idEncabezado,
        "automatizacion": rows[0].automatizacion,
        "fechaCargue": str(rows[0].fechaCargue),
        "totalRegistros": rows[0].totalRegistros,
        "detalles": []
    }

    for row in rows:
        if row.idDetalle is not None:
            encabezado["detalles"].append({
                "idDetalle": row.idDetalle,
                "cedula": row.cedula,
                "placaVehiculo": row.placaVehiculo,
                "tipoServicio": row.tipoServicio,
                "estadoVehiculo": row.estadoVehiculo,
                "claseVehiculo": row.claseVehiculo,
                "marca": row.marca,
                "modelo": row.modelo,
                "numeroSerie": row.numeroSerie,
                "numeroChasis": row.numeroChasis,
                "cilindraje": row.cilindraje,
                "tipoCombustible": row.tipoCombustible,
                "autoridadTransito": row.autoridadTransito,
                "linea": row.linea,
                "color": row.color,
                "numeroMotor": row.numeroMotor,
                "numeroVIN": row.numeroVIN,
                "tipoCarroceria": row.tipoCarroceria,
                "polizaSOAT": row.polizaSOAT,
                "revisionTecnomecanica": row.revisionTecnomecanica,
                "limitacionesPropiedad": row.limitacionesPropiedad,
                "garantiasAFavorDe": row.garantiasAFavorDe
            })

    return encabezado


def obtener_automatizacionCCRunt():
    """
    Retorna la siguiente tupla (idEncabezado, cedula) pendiente.
    Lanza excepción si hay un error, o devuelve None si no hay más cédulas.
    """
    filas, error = obtener_CC_aConsultarRunt()
    if error:
        raise Exception(f"Error al consultar próxima cédula: {error}")
    if not filas:
        return None
    return filas[0]

def listar_detalles_por_encabezado_paginadoBLLRunt(id_encabezado: int, offset: int = 0, limit: int = 50, cedula: str | None = None):
    total = contar_detalles_por_encabezadoRunt(id_encabezado, cedula)
    rows = obtener_detalles_por_encabezado_paginadoRunt(id_encabezado, offset, limit, cedula)
    return {"rows": rows, "total": total}

def resumen_encabezadoBLLRunt(id_encabezado: int):
    total = contar_total_por_encabezadoRunt(id_encabezado)
    procesados = contar_procesados_por_encabezadoRunt(id_encabezado)
    return {"idEncabezado": id_encabezado, "totalRegistros": total, "procesados": procesados}

def listar_encabezados_paginado_Runt_bll(offset: int, limit: int):
    rows = obtener_encabezados_paginado_Runt(offset, limit)
    if rows is None:
        raise Exception("Error al obtener encabezados paginados")

    resultados = []
    for row in rows:
        if not row:
            continue
        total = getattr(row, "totalRegistros", 0) or 0
        ingresados = getattr(row, "detallesIngresados", 0) or 0
        if getattr(row, "estado", None) == "Pausado":
            estado = "Pausado"
        else:
            porcentaje = (ingresados / total * 100) if total else 0
            estado = (
                "No iniciada" if ingresados == 0 else
                "Finalizada" if ingresados >= total else
                f"En progreso ({int(porcentaje)}%)"
            )

        resultados.append({
            "idEncabezado": row.idEncabezado,
            "automatizacion": row.automatizacion,
            "fechaCargue": str(row.fechaCargue),
            "totalRegistros": total,
            "detallesIngresados": ingresados,
            "estado": estado,
            "nombreUsuario": getattr(row, "nombreUsuario", "Desconocido")
        })

    total_enc = contar_encabezados_Runt()
    return {"rows": resultados, "total": total_enc}

#------------RUES -----------------------
def listar_automatizaciones_estadoRues():
    """
    Lista todas las automatizaciones para el módulo Rues, calculando el estado de avance.

    Detalles:
    - Llama a la función DAL `obtener_automatizacionesRues()` para obtener registros.
    - Si ocurre error (rows es None), lanza excepción para alertar fallo en capa de datos.
    - Recorre cada fila, validando que no sea None y que los campos relevantes no sean nulos.
    - Calcula el porcentaje de detalles ingresados sobre el total de registros.
    - Define el estado basado en:
        * "No iniciada" si detalles ingresados = 0.
        * "Finalizada" si detalles ingresados >= total registros.
        * "En progreso (x%)" en caso intermedio.
    - Construye una lista de diccionarios con la información resumida para cada automatización.
    - Retorna la lista lista para ser consumida en la capa API.
    """
    rows, error = obtener_automatizacionesRues()
    
    if rows is None:
        raise Exception(f"Error al obtener automatizaciones: {error}")

    resultados = []
    for row in rows:
        if not row or row.totalRegistros is None or row.detallesIngresados is None:
            continue

        if row.estado and row.estado == "Pausado":
            estado = "Pausado"
        else:
            porcentaje = (row.detallesIngresados / row.totalRegistros) * 100 if row.totalRegistros else 0
            estado = (
                "No iniciada" if row.detallesIngresados == 0 else
                "Finalizada" if row.detallesIngresados >= row.totalRegistros else
                f"En progreso ({int(porcentaje)}%)"
        )

        resultados.append({
            "idEncabezado": row.idEncabezado,
            "automatizacion": row.automatizacion,
            "fechaCargue": str(row.fechaCargue),
            "totalRegistros": row.totalRegistros,
            "detallesIngresados": row.detallesIngresados,
            "estado": estado,
            "nombreUsuario": getattr(row, "nombreUsuario", "Desconocido")
        })

    return resultados


def obtener_automatizacionRues(id_encabezado: int):
    rows, error = obtener_automatizacion_por_idRues(id_encabezado)
    
    if error or not rows:
        return None

    encabezado = {
        "idEncabezado": rows[0].idEncabezado,
        "automatizacion": rows[0].automatizacion,
        "fechaCargue": str(rows[0].fechaCargue),
        "totalRegistros": rows[0].totalRegistros,
        "detalles": []
    }

    for row in rows:
        if row.idDetalle is not None:
            encabezado["detalles"].append({
                "idDetalle": row.idDetalle,
                "cedula": row.cedula,
                "nombre": row.nombre,
                "identificacion": row.identificacion,
                "categoria": row.categoria,
                "camaraComercio": row.camaraComercio,
                "numeroMatricula": row.numeroMatricula,
                "actividadEconomica": row.actividadEconomica
            })

    return encabezado

def obtener_automatizacionCCRues():
    """
    Retorna la siguiente tupla (idEncabezado, cedula) pendiente.
    Lanza excepción si hay un error, o devuelve None si no hay más cédulas.
    """
    filas, error = obtener_CC_aConsultarRues()
    if error:
        raise Exception(f"Error al consultar próxima cédula: {error}")
    if not filas:
        return None
    return filas[0]


def refrescar_automatizacion_estado_por_id(id_encabezado: int):
    """
    Refresca y calcula el estado resumido de una automatización por su ID.

    Detalles:
    - Llama a DAL `obtener_automatizacion_por_id(id_encabezado)` para traer datos.
    - Si hay error o no hay filas, retorna None para indicar fallo o inexistencia.
    - Cuenta total registros y filtra detalles válidos (matricula no vacía).
    - Calcula porcentaje completado.
    - Determina estado:
      * "No iniciada" si 0 completados.
      * "Finalizada" si completados >= total.
      * "En progreso (x%)" si parcialmente completada.
    - Retorna diccionario con información resumida y estado calculado.
    """
    rows, error = obtener_automatizacion_por_id(id_encabezado)
    if error or not rows:
        return None

    total = rows[0].totalRegistros
    detallesValidos = [
        r for r in rows if r.matricula and r.matricula.strip() != ""
    ]
    completados = len(detallesValidos)
    porcentaje = (completados / total) * 100 if total else 0

    estado = (
        "No iniciada" if completados == 0 else
        "Finalizada" if completados >= total else
        f"En progreso ({int(porcentaje)}%)"
    )

    return {
        "idEncabezado": rows[0].idEncabezado,
        "automatizacion": rows[0].automatizacion,
        "fechaCargue": str(rows[0].fechaCargue),
        "totalRegistros": total,
        "detallesIngresados": completados,
        "estado": estado
    }

def listar_detalles_por_encabezado_paginadoBLLRues(id_encabezado: int, offset: int = 0, limit: int = 50, cedula: str | None = None):
    total = contar_detalles_por_encabezadoRues(id_encabezado, cedula)
    rows = obtener_detalles_por_encabezado_paginadoRues(id_encabezado, offset, limit, cedula)
    return {"rows": rows, "total": total}

def resumen_encabezadoBLLRues(id_encabezado: int):
    total = contar_total_por_encabezadoRues(id_encabezado)
    procesados = contar_procesados_por_encabezadoRues(id_encabezado)
    return {"idEncabezado": id_encabezado, "totalRegistros": total, "procesados": procesados}

def listar_encabezados_paginado_Rues_bll(offset: int, limit: int):
    rows = obtener_encabezados_paginado_Rues(offset, limit)
    if rows is None:
        raise Exception("Error al obtener encabezados paginados")

    resultados = []
    for row in rows:
        if not row:
            continue
        total = getattr(row, "totalRegistros", 0) or 0
        ingresados = getattr(row, "detallesIngresados", 0) or 0
        if getattr(row, "estado", None) == "Pausado":
            estado = "Pausado"
        else:
            porcentaje = (ingresados / total * 100) if total else 0
            estado = (
                "No iniciada" if ingresados == 0 else
                "Finalizada" if ingresados >= total else
                f"En progreso ({int(porcentaje)}%)"
            )

        resultados.append({
            "idEncabezado": row.idEncabezado,
            "automatizacion": row.automatizacion,
            "fechaCargue": str(row.fechaCargue),
            "totalRegistros": total,
            "detallesIngresados": ingresados,
            "estado": estado,
            "nombreUsuario": getattr(row, "nombreUsuario", "Desconocido")
        })

    total_enc = contar_encabezados_Rues()
    return {"rows": resultados, "total": total_enc}

#-------------- SIMIT -------------------------------------------------
def listar_automatizaciones_estadoSimit():
    """
    Lista todas las automatizaciones para el módulo SIMIT, con cálculo de estado y porcentaje de progreso.

    Detalles:
    - Llama a la función DAL `obtener_automatizacionesSimit()` para traer los datos.
    - Si ocurre error (rows es None), lanza excepción para indicar fallo en acceso a datos.
    - Itera sobre cada registro válido, ignorando filas nulas o con datos incompletos.
    - Calcula el porcentaje de detalles ingresados sobre el total.
    - Define el estado según:
        * "No iniciada" si detallesIngresados == 0.
        * "Finalizada" si detallesIngresados >= totalRegistros.
        * "En progreso (x%)" en cualquier otro caso.
    - Arma una lista de diccionarios con información relevante para cada automatización.
    - Devuelve dicha lista para consumo de la capa API.
    """
    rows, error = obtener_automatizacionesSimit()
    
    if rows is None:
        raise Exception(f"Error al obtener automatizaciones: {error}")

    resultados = []
    for row in rows:
        if not row or row.totalRegistros is None or row.detallesIngresados is None:
            continue

        if row.estado and row.estado == "Pausado":
            estado = "Pausado"
        else:
            porcentaje = (row.detallesIngresados / row.totalRegistros) * 100 if row.totalRegistros else 0
            estado = (
                "No iniciada" if row.detallesIngresados == 0 else
                "Finalizada" if row.detallesIngresados >= row.totalRegistros else
                f"En progreso ({int(porcentaje)}%)"
        )

        resultados.append({
            "idEncabezado": row.idEncabezado,
            "automatizacion": row.automatizacion,
            "fechaCargue": str(row.fechaCargue),
            "totalRegistros": row.totalRegistros,
            "detallesIngresados": row.detallesIngresados,
            "estado": estado,
            "nombreUsuario": getattr(row, "nombreUsuario", "Desconocido")
        })

    return resultados


def obtener_automatizacionSimit(id_encabezado: int):
    """
    Obtiene una automatización SIMIT completa con sus detalles asociados por ID.

    Detalles:
    - Llama a DAL `obtener_automatizacion_por_idSimit()` para traer los registros.
    - Si no existen registros, retorna None para indicar ausencia.
    - Construye un diccionario `encabezado` con los datos generales de la automatización.
    - Llena la lista `detalles` con información detallada de cada registro:
      * idDetalle, cedula, tipo, placa y secretaria.
    - Devuelve la estructura lista para la capa API o frontend.
    """
    rows = obtener_automatizacion_por_idSimit(id_encabezado)
    if not rows:
        return None

    encabezado = {
        "idEncabezado": rows[0].idEncabezado,
        "automatizacion": rows[0].automatizacion,
        "fechaCargue": str(rows[0].fechaCargue),
        "totalRegistros": rows[0].totalRegistros,
        "detalles": []
    }

    for row in rows:
        if row.idDetalle is not None:
            encabezado["detalles"].append({
                "idDetalle": row.idDetalle,
                "cedula": row.cedula,
                "tipo": row.tipo,
                "placa": row.placa,
                "secretaria": row.secretaria
            })

    return encabezado


def obtener_automatizacionCCSimit():
    """
    Retorna la siguiente tupla (idEncabezado, cedula) pendiente.
    Lanza excepción si hay un error, o devuelve None si no hay más cédulas.
    """
    filas, error = obtener_CC_aConsultarSimit()
    if error:
        raise Exception(f"Error al consultar próxima cédula: {error}")
    if not filas:
        return None
    return filas[0]

def listar_detalles_por_encabezado_paginadoBLLSimit(id_encabezado: int, offset: int = 0, limit: int = 50, cedula: str | None = None):
    total = contar_detalles_por_encabezadoSimit(id_encabezado, cedula)
    rows = obtener_detalles_por_encabezado_paginadoSimit(id_encabezado, offset, limit, cedula)
    return {"rows": rows, "total": total}

def resumen_encabezadoBLLSimit(id_encabezado: int):
    total = contar_total_por_encabezadoSimit(id_encabezado)
    procesados = contar_procesados_por_encabezadoSimit(id_encabezado)
    return {"idEncabezado": id_encabezado, "totalRegistros": total, "procesados": procesados}

def listar_encabezados_paginado_Simit_bll(offset: int, limit: int):
    rows = obtener_encabezados_paginado_Simit(offset, limit)
    if rows is None:
        raise Exception("Error al obtener encabezados paginados")

    resultados = []
    for row in rows:
        if not row:
            continue
        total = getattr(row, "totalRegistros", 0) or 0
        ingresados = getattr(row, "detallesIngresados", 0) or 0
        if getattr(row, "estado", None) == "Pausado":
            estado = "Pausado"
        else:
            porcentaje = (ingresados / total * 100) if total else 0
            estado = (
                "No iniciada" if ingresados == 0 else
                "Finalizada" if ingresados >= total else
                f"En progreso ({int(porcentaje)}%)"
            )

        resultados.append({
            "idEncabezado": row.idEncabezado,
            "automatizacion": row.automatizacion,
            "fechaCargue": str(row.fechaCargue),
            "totalRegistros": total,
            "detallesIngresados": ingresados,
            "estado": estado,
            "nombreUsuario": getattr(row, "nombreUsuario", "Desconocido")
        })

    total_enc = contar_encabezados_Simit()
    return {"rows": resultados, "total": total_enc}

#-------------- VIGILANCIA  ----------------------------------------------
def listar_automatizaciones_estadoVigilancia():
    rows, error = obtener_automatizacionesVigilancia()
    
    if rows is None:
        raise Exception(f"Error al obtener automatizaciones: {error}")

    resultados = []
    for row in rows:
        if not row or row.totalRegistros is None or row.detallesIngresados is None:
            continue

        if row.estado and row.estado == "Pausado":
            estado = "Pausado"
        else:
            porcentaje = (row.detallesIngresados / row.totalRegistros) * 100 if row.totalRegistros else 0
            estado = (
                "No iniciada" if row.detallesIngresados == 0 else
                "Finalizada" if row.detallesIngresados >= row.totalRegistros else
                f"En progreso ({int(porcentaje)}%)"
        )

        resultados.append({
            "idEncabezado": row.idEncabezado,
            "automatizacion": row.automatizacion,
            "fechaCargue": str(row.fechaCargue),
            "totalRegistros": row.totalRegistros,
            "detallesIngresados": row.detallesIngresados,
            "estado": estado,
            "nombreUsuario": getattr(row, "nombreUsuario", "Desconocido")
        })

    return resultados


def obtener_automatizacionVigilancia(id_encabezado: int):
    rows = obtener_automatizacion_por_idVigilancia(id_encabezado)
    if not rows:
        return None

    encabezado = {
        "idEncabezado": rows[0].idEncabezado,
        "automatizacion": rows[0].automatizacion,
        "fechaCargue": str(rows[0].fechaCargue),
        "totalRegistros": rows[0].totalRegistros,
        "detalles": []
    }

    for row in rows:
        if row.idDetalle is not None:
            encabezado["detalles"].append({
                "idDetalle": row.idDetalle,
                "radicado": row.radicado,
                "fechaActuacion": row.fechaActuacion,
                "actuacion": row.actuacion,
                "anotacion": row.anotacion,
                "fechaIniciaTermino": row.fechaIniciaTermino,
                "fechaFinalizaTermino": row.fechaFinalizaTermino,
                "fechaRegistro": row.fechaRegistro,
                "radicadoNuevo": row.radicadoNuevo
            })

    return encabezado


def obtener_automatizacionRadicadoVigilancia():
    """
    Retorna la siguiente tupla (radicado, fechaInicial, fechaFinal) pendiente.
    Lanza excepción si hay un error, o devuelve None si no hay más radicados.
    """
    filas, error = obtener_Radicado_aConsultarVigilancia()
    if error:
        raise Exception(f"Error al consultar próximo radicado: {error}")
    if not filas:
        return None
    return filas[0]

def listar_detalles_por_encabezado_paginadoBLLVigilancia(id_encabezado: int, offset: int = 0, limit: int = 50, radicado: str | None = None):
    total = contar_detalles_por_encabezadoVigilancia(id_encabezado, radicado)
    rows = obtener_detalles_por_encabezado_paginadoVigilancia(id_encabezado, offset, limit, radicado)
    return {"rows": rows, "total": total}

def resumen_encabezadoBLLVigilancia(id_encabezado: int):
    total = contar_total_por_encabezadoVigilancia(id_encabezado)
    procesados = contar_procesados_por_encabezadoVigilancia(id_encabezado)
    return {"idEncabezado": id_encabezado, "totalRegistros": total, "procesados": procesados}

def listar_encabezados_paginado_Vigilancia_bll(offset: int, limit: int):
    rows = obtener_encabezados_paginado_Vigilancia(offset, limit)
    if rows is None:
        raise Exception("Error al obtener encabezados paginados")

    resultados = []
    for row in rows:
        if not row:
            continue
        total = getattr(row, "totalRegistros", 0) or 0
        ingresados = getattr(row, "detallesIngresados", 0) or 0
        if getattr(row, "estado", None) == "Pausado":
            estado = "Pausado"
        else:
            porcentaje = (ingresados / total * 100) if total else 0
            estado = (
                "No iniciada" if ingresados == 0 else
                "Finalizada" if ingresados >= total else
                f"En progreso ({int(porcentaje)}%)"
            )

        resultados.append({
            "idEncabezado": row.idEncabezado,
            "automatizacion": row.automatizacion,
            "fechaCargue": str(row.fechaCargue),
            "totalRegistros": total,
            "detallesIngresados": ingresados,
            "estado": estado,
            "nombreUsuario": getattr(row, "nombreUsuario", "Desconocido")
        })

    total_enc = contar_encabezados_Vigilancia()
    return {"rows": resultados, "total": total_enc}

#-------------- CAMARA COMERCIO --------------
def listar_automatizaciones_estadoCamaraComercio():

    rows, error = obtener_automatizacionesCamaraComercio()
    
    if rows is None:
        raise Exception(f"Error al obtener automatizaciones: {error}")

    resultados = []
    for row in rows:
        if not row or row.totalRegistros is None or row.detallesIngresados is None:
            continue

        if row.estado and row.estado == "Pausado":
            estado = "Pausado"
        else:
            porcentaje = (row.detallesIngresados / row.totalRegistros) * 100 if row.totalRegistros else 0
            estado = (
                "No iniciada" if row.detallesIngresados == 0 else
                "Finalizada" if row.detallesIngresados >= row.totalRegistros else
                f"En progreso ({int(porcentaje)}%)"
        )

        resultados.append({
            "idEncabezado": row.idEncabezado,
            "automatizacion": row.automatizacion,
            "fechaCargue": str(row.fechaCargue),
            "totalRegistros": row.totalRegistros,
            "detallesIngresados": row.detallesIngresados,
            "estado": estado,
            "nombreUsuario": getattr(row, "nombreUsuario", "Desconocido")
        })

    return resultados


def obtener_automatizacionCamaraComercio(id_encabezado: int):
    rows = obtener_automatizacion_por_idCamaraComercio(id_encabezado)
    if not rows:
        return None

    encabezado = {
        "idEncabezado": rows[0].idEncabezado,
        "automatizacion": rows[0].automatizacion,
        "fechaCargue": str(rows[0].fechaCargue),
        "totalRegistros": rows[0].totalRegistros,
        "detalles": []
    }

    for row in rows:
        if row.idDetalle is not None:
            encabezado["detalles"].append({
                "idDetalle": row.idDetalle,
                "cedula": row.cedula,
                "identificacion": row.identificacion,
                "primerNombre": row.primerNombre,
                "segundoNombre": row.segundoNombre,
                "primerApellido": row.primerApellido,
                "segundoApellido": row.segundoApellido,
                "direccion": row.direccion,
                "pais": row.pais,
                "departamento": row.departamento,
                "municipio": row.municipio,
                "telefono": row.telefono,
                "correo": row.correo
            })

    return encabezado


def obtener_automatizacionCCCamaraComercio():
    """
    Retorna la siguiente tupla (idEncabezado, cedula) pendiente.
    Lanza excepción si hay un error, o devuelve None si no hay más cédulas.
    """
    filas, error = obtener_CC_aConsultarCamaraComercio()
    if error:
        raise Exception(f"Error al consultar próxima cédula: {error}")
    if not filas:
        return None
    return filas[0]

def listar_detalles_por_encabezado_paginadoBLLCamaraComercio(id_encabezado: int, offset: int = 0, limit: int = 50, cedula: str | None = None):
    total = contar_detalles_por_encabezadoCamaraComercio(id_encabezado, cedula)
    rows = obtener_detalles_por_encabezado_paginadoCamaraComercio(id_encabezado, offset, limit, cedula)
    return {"rows": rows, "total": total}

def resumen_encabezadoBLLCamaraComercio(id_encabezado: int):
    total = contar_total_por_encabezadoCamaraComercio(id_encabezado)
    procesados = contar_procesados_por_encabezadoCamaraComercio(id_encabezado)
    return {"idEncabezado": id_encabezado, "totalRegistros": total, "procesados": procesados}

def listar_encabezados_paginado_CamaraComercio_bll(offset: int, limit: int):
    rows = obtener_encabezados_paginado_CamaraComercio(offset, limit)
    if rows is None:
        raise Exception("Error al obtener encabezados paginados")

    resultados = []
    for row in rows:
        if not row:
            continue
        total = getattr(row, "totalRegistros", 0) or 0
        ingresados = getattr(row, "detallesIngresados", 0) or 0
        if getattr(row, "estado", None) == "Pausado":
            estado = "Pausado"
        else:
            porcentaje = (ingresados / total * 100) if total else 0
            estado = (
                "No iniciada" if ingresados == 0 else
                "Finalizada" if ingresados >= total else
                f"En progreso ({int(porcentaje)}%)"
            )

        resultados.append({
            "idEncabezado": row.idEncabezado,
            "automatizacion": row.automatizacion,
            "fechaCargue": str(row.fechaCargue),
            "totalRegistros": total,
            "detallesIngresados": ingresados,
            "estado": estado,
            "nombreUsuario": getattr(row, "nombreUsuario", "Desconocido")
        })

    total_enc = contar_encabezados_CamaraComercio()
    return {"rows": resultados, "total": total_enc}

#-------------- JURIDICO --------------
def listar_automatizaciones_estadoJuridico():

    rows, error = obtener_automatizacionesJuridico()
    
    if rows is None:
        raise Exception(f"Error al obtener automatizaciones: {error}")

    resultados = []
    for row in rows:
        if not row or row.totalRegistros is None or row.detallesIngresados is None:
            continue

        if row.estado and row.estado == "Pausado":
            estado = "Pausado"
        else:
            porcentaje = (row.detallesIngresados / row.totalRegistros) * 100 if row.totalRegistros else 0
            estado = (
                "No iniciada" if row.detallesIngresados == 0 else
                "Finalizada" if row.detallesIngresados >= row.totalRegistros else
                f"En progreso ({int(porcentaje)}%)"
        )

        resultados.append({
            "idEncabezado": row.idEncabezado,
            "automatizacion": row.automatizacion,
            "fechaCargue": str(row.fechaCargue),
            "totalRegistros": row.totalRegistros,
            "detallesIngresados": row.detallesIngresados,
            "estado": estado,
            "nombreUsuario": getattr(row, "nombreUsuario", "Desconocido")
        })

    return resultados


def obtener_automatizacionJuridico(id_encabezado: int):
   
    rows = obtener_automatizacion_por_idJuridico(id_encabezado)
    if not rows:
        return None

    encabezado = {
        "idEncabezado": rows[0].idEncabezado,
        "automatizacion": rows[0].automatizacion,
        "fechaCargue": str(rows[0].fechaCargue),
        "totalRegistros": rows[0].totalRegistros,
        "detalles": []
    }

    for row in rows:
        if row.idDetalle is not None:
            encabezado["detalles"].append({
                "idDetalle": row.idDetalle,
                "nombreCompleto": row.nombreCompleto,
                "departamento": row.departamento,
                "ciudad": row.ciudad,
                "especialidad": row.especialidad
            })

    return encabezado

def procesar_archivo_excel(encabezado: EncabezadoModel) -> int:
    detalles_validos = [d for d in encabezado.detalles if d.nombreCompleto and d.nombreCompleto.strip()]
    
    encabezado.totalRegistros = len(detalles_validos)

    idEncabezado = insertar_encabezado(encabezado)
    if not idEncabezado or idEncabezado == -1:
        raise Exception("❌ Error al insertar encabezado. No se puede continuar con los detalles.")
    
    for detalle in detalles_validos:
        insertar_detalle(idEncabezado, detalle)

    return idEncabezado

def enviar_correo_finalizacionJuridico(id_usuario: int):
    correo_destino = obtener_correo_usuarioJuridico(id_usuario)
    if not correo_destino:
        print(f"❌ No se encontró correo para usuario {id_usuario}")
        return False

    asunto = "Automatización completada"
    cuerpo = f"""
    Hola,

    La automatización JURIDICO ha finalizado exitosamente.

    Puedes revisar los resultados en el sistema.

    Saludos,
    Sistema de Automatización.
    """

    mensaje = MIMEMultipart()
    mensaje["From"] = REMITENTE
    mensaje["To"] = correo_destino
    mensaje["Subject"] = asunto
    mensaje.attach(MIMEText(cuerpo, "plain"))

    try:
        with smtplib.SMTP(SERVER, PORT) as servidor:
            servidor.starttls()
            servidor.login(REMITENTE, PASSWORD)
            servidor.send_message(mensaje)
            print(f"📨 Correo enviado a {correo_destino}")
            return True
    except Exception as e:
        import traceback
        traceback.print_exc()
        return False

def enviar_correo_finalizacion_por_encabezado(idEncabezado: int) -> bool:
    """
    Envía el correo de finalización solo si no se ha enviado previamente.
    """
    if correo_ya_enviado(idEncabezado):
        print(f"⚠️ Correo ya enviado previamente para encabezado {idEncabezado}")
        return True  

    id_usuario = obtener_idUsuario_por_encabezado(idEncabezado)
    if id_usuario is None:
        print(f"No se encontró idUsuario para encabezado {idEncabezado}")
        return False

    enviado = enviar_correo_finalizacionJuridico(id_usuario)
    if enviado:
        marcar_correo_enviado(idEncabezado)
    return enviado

#---------- PAUSAR-------------------------------
def pausar_encabezado(id_encabezado: int) -> bool:
    ok1 = marcar_pausa_encabezado(id_encabezado, datetime.now())
    ok2 = pausar_detalle_encabezado(id_encabezado)
    return ok1 and ok2

def reanudar_encabezado(id_encabezado: int) -> bool:
    ok1 = quitar_pausa_encabezado(id_encabezado)
    ok2 = reanudar_detalle_encabezado(id_encabezado)
    return ok1 and ok2

#-------------- TYBA --------------
def listar_automatizaciones_estadoTyba():
    rows, error = obtener_automatizacionesTyba()
    
    if rows is None:
        raise Exception(f"Error al obtener automatizaciones: {error}")

    resultados = []
    for row in rows:
        if not row or row.totalRegistros is None or row.detallesIngresados is None:
            continue

        if row.estado and row.estado == "Pausado":
            estado = "Pausado"
        else:
            porcentaje = (row.detallesIngresados / row.totalRegistros) * 100 if row.totalRegistros else 0
            estado = (
                "No iniciada" if row.detallesIngresados == 0 else
                "Finalizada" if row.detallesIngresados >= row.totalRegistros else
                f"En progreso ({int(porcentaje)}%)"
        )

        resultados.append({
            "idEncabezado": row.idEncabezado,
            "automatizacion": row.automatizacion,
            "fechaCargue": str(row.fechaCargue),
            "totalRegistros": row.totalRegistros,
            "detallesIngresados": row.detallesIngresados,
            "estado": estado,
            "nombreUsuario": getattr(row, "nombreUsuario", "Desconocido")
        })

    return resultados


def obtener_automatizacionTyba(id_encabezado: int):
    rows = obtener_automatizacion_por_idTyba(id_encabezado)
    if not rows:
        return None

    encabezado = {
        "idEncabezado": rows[0].idEncabezado,
        "automatizacion": rows[0].automatizacion,
        "fechaCargue": str(rows[0].fechaCargue),
        "totalRegistros": rows[0].totalRegistros,
        "detalles": []
    }

    for row in rows:
        if row.idDetalle is not None:
            encabezado["detalles"].append({
                "idDetalle": row.idDetalle,
                "cedula": row.cedula,
                "radicado": row.radicado,
                "proceso": row.proceso,
                "departamento": row.departamento,
                "coorporacion": row.coorporacion,
                "distrito": row.distrito,
                "despacho": row.despacho,
                "telefono": row.telefono,
                "correo": row.correo,
                "fechaProvidencia": row.fechaProvidencia,
                "tipoProceso": row.tipoProceso,
                "subclaseProceso": row.subclaseProceso,
                "ciudad": row.ciudad,
                "especialidad": row.especialidad,
                "numeroDespacho": row.numeroDespacho,
                "direccion": row.direccion,
                "celular": row.celular,
                "fechaPublicacion": row.fechaPublicacion,
                "sujetos": row.sujetos,
                "actuaciones": row.actuaciones
            })

    return encabezado


def obtener_automatizacionCCTyba():
    """
    Retorna la siguiente tupla (idEncabezado, cedula) pendiente.
    Lanza excepción si hay un error, o devuelve None si no hay más cédulas.
    """
    filas, error = obtener_CC_aConsultarTyba()
    if error:
        raise Exception(f"Error al consultar próxima cédula: {error}")
    if not filas:
        return None
    return filas[0]

def listar_detalles_por_encabezado_paginadoBLLTyba(id_encabezado: int, offset: int = 0, limit: int = 50, cedula: str | None = None):
    total = contar_detalles_por_encabezadoTyba(id_encabezado, cedula)
    rows = obtener_detalles_por_encabezado_paginadoTyba(id_encabezado, offset, limit, cedula)
    return {"rows": rows, "total": total}

def resumen_encabezadoBLLTyba(id_encabezado: int):
    total = contar_total_por_encabezadoTyba(id_encabezado)
    procesados = contar_procesados_por_encabezadoTyba(id_encabezado)
    return {"idEncabezado": id_encabezado, "totalRegistros": total, "procesados": procesados}

def listar_encabezados_paginado_Tyba_bll(offset: int, limit: int):
    rows = obtener_encabezados_paginado_Tyba(offset, limit)
    if rows is None:
        raise Exception("Error al obtener encabezados paginados")

    resultados = []
    for row in rows:
        if not row:
            continue
        total = getattr(row, "totalRegistros", 0) or 0
        ingresados = getattr(row, "detallesIngresados", 0) or 0
        if getattr(row, "estado", None) == "Pausado":
            estado = "Pausado"
        else:
            porcentaje = (ingresados / total * 100) if total else 0
            estado = (
                "No iniciada" if ingresados == 0 else
                "Finalizada" if ingresados >= total else
                f"En progreso ({int(porcentaje)}%)"
            )

        resultados.append({
            "idEncabezado": row.idEncabezado,
            "automatizacion": row.automatizacion,
            "fechaCargue": str(row.fechaCargue),
            "totalRegistros": total,
            "detallesIngresados": ingresados,
            "estado": estado,
            "nombreUsuario": getattr(row, "nombreUsuario", "Desconocido")
        })

    total_enc = contar_encabezados_Tyba()
    return {"rows": resultados, "total": total_enc}

#-------------- VIGENCIA --------------
def listar_automatizaciones_estadoVigencia():

    rows, error = obtener_automatizacionesVigencia()
    
    if rows is None:
        raise Exception(f"Error al obtener automatizaciones: {error}")

    resultados = []
    for row in rows:
        if not row or row.totalRegistros is None or row.detallesIngresados is None:
            continue

        if row.estado and row.estado == "Pausado":
            estado = "Pausado"
        else:
            porcentaje = (row.detallesIngresados / row.totalRegistros) * 100 if row.totalRegistros else 0
            estado = (
                "No iniciada" if row.detallesIngresados == 0 else
                "Finalizada" if row.detallesIngresados >= row.totalRegistros else
                f"En progreso ({int(porcentaje)}%)"
        )

        resultados.append({
            "idEncabezado": row.idEncabezado,
            "automatizacion": row.automatizacion,
            "fechaCargue": str(row.fechaCargue),
            "totalRegistros": row.totalRegistros,
            "detallesIngresados": row.detallesIngresados,
            "estado": estado,
            "nombreUsuario": getattr(row, "nombreUsuario", "Desconocido")
        })

    return resultados


def obtener_automatizacionVigencia(id_encabezado: int):
   
    rows = obtener_automatizacion_por_idVigencia(id_encabezado)
    if not rows:
        return None

    encabezado = {
        "idEncabezado": rows[0].idEncabezado,
        "automatizacion": rows[0].automatizacion,
        "fechaCargue": str(rows[0].fechaCargue),
        "totalRegistros": rows[0].totalRegistros,
        "detalles": []
    }

    for row in rows:
        if row.idDetalle is not None:
            encabezado["detalles"].append({
                "idDetalle": row.idDetalle,
                "nombre": row.nombre,
                "cedula": row.cedula,
                "vigencia": row.vigencia,
                "fechaConsulta": row.fechaConsulta
            })

    return encabezado

def procesar_archivo_excelVigencia(encabezado: EncabezadoModel) -> int:
    detalles_validos = [d for d in encabezado.detalles if d.cedula and d.cedula.strip()]
    
    encabezado.totalRegistros = len(detalles_validos)

    idEncabezado = insertar_encabezadoVigencia(encabezado)
    if not idEncabezado or idEncabezado == -1:
        raise Exception("❌ Error al insertar encabezado. No se puede continuar con los detalles.")
    
    for detalle in detalles_validos:
        insertar_detalleVigencia(idEncabezado, detalle)

    return idEncabezado

def enviar_correo_finalizacionVigencia(id_usuario: int):
    correo_destino = obtener_correo_usuarioVigencia(id_usuario)
    if not correo_destino:
        print(f"❌ No se encontró correo para usuario {id_usuario}")
        return False

    asunto = "Automatización completada"
    cuerpo = f"""
    Hola,

    La automatización VIGENCIA ha finalizado exitosamente.

    Puedes revisar los resultados en el sistema.

    Saludos,
    Sistema de Automatización.
    """

    mensaje = MIMEMultipart()
    mensaje["From"] = REMITENTE
    mensaje["To"] = correo_destino
    mensaje["Subject"] = asunto
    mensaje.attach(MIMEText(cuerpo, "plain"))

    try:
        with smtplib.SMTP(SERVER, PORT) as servidor:
            servidor.starttls()
            servidor.login(REMITENTE, PASSWORD)
            servidor.send_message(mensaje)
            print(f"📨 Correo enviado a {correo_destino}")
            return True
    except Exception as e:
        import traceback
        traceback.print_exc()
        return False

def enviar_correo_finalizacion_por_encabezadoVigencia(idEncabezado: int) -> bool:
    """
    Envía el correo de finalización solo si no se ha enviado previamente.
    """
    if correo_ya_enviadoVigencia(idEncabezado):
        print(f"⚠️ Correo ya enviado previamente para encabezado {idEncabezado}")
        return True  

    id_usuario = obtener_idUsuario_por_encabezadoVigencia(idEncabezado)
    if id_usuario is None:
        print(f"No se encontró idUsuario para encabezado {idEncabezado}")
        return False

    enviado = enviar_correo_finalizacionVigencia(id_usuario)
    if enviado:
        marcar_correo_enviadoVigencia(idEncabezado)
    return enviado

#---------- PAUSAR-------------------------------
def pausar_encabezadoVigencia(id_encabezado: int) -> bool:
    ok1 = marcar_pausa_encabezadoVigencia(id_encabezado, datetime.now())
    ok2 = pausar_detalle_encabezadoVigencia(id_encabezado)
    return ok1 and ok2

def reanudar_encabezadoVigencia(id_encabezado: int) -> bool:
    ok1 = quitar_pausa_encabezadoVigencia(id_encabezado)
    ok2 = reanudar_detalle_encabezadoVigencia(id_encabezado)
    return ok1 and ok2