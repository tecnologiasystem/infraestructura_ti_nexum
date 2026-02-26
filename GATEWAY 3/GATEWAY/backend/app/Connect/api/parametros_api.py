from fastapi import APIRouter, Query
from app.bll.parametros_bll import obtener_parametros, calcular_tokens_usados

router = APIRouter()

@router.get("/consultar")
def consultar(modulo: str = Query(None), nombre: str = Query(None)):
    return obtener_parametros(modulo, nombre)

@router.get("/tokens-usados")
def obtener_tokens_usados():
    return calcular_tokens_usados()