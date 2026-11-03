"""
Sistema de Gestión Software FJ
Proyecto Fase 4 - Programación (UNAD)

Todo el sistema trabaja en memoria (listas), sin bases de datos.
Uso:
    python main.py          -> ejecuta la simulación automática
    python main.py --menu   -> abre el menú interactivo
"""
import logging
import re
import sys
from abc import ABC, abstractmethod
from datetime import datetime, timedelta

IVA = 0.19  # IVA aplicado a todos los servicios


# =====================================================
# 1. EXCEPCIONES PERSONALIZADAS
# =====================================================
class ErrorSistemaFJ(Exception):
    """Clase base: todas las excepciones del sistema heredan de esta."""


class ClienteInvalidoError(ErrorSistemaFJ):
    """Datos del cliente incorrectos o cliente duplicado/inexistente."""


class ServicioInvalidoError(ErrorSistemaFJ):
    """Parámetros del servicio incorrectos."""


class ReservaInvalidaError(ErrorSistemaFJ):
    """No se pudo crear la reserva."""


# =====================================================
# 2. REGISTRO DE ERRORES (errores.log)
# =====================================================
logger = logging.getLogger("software_fj")
logger.setLevel(logging.ERROR)
if not logger.handlers:
    _archivo = logging.FileHandler("errores.log", encoding="utf-8")
    _archivo.setFormatter(
        logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s", "%Y-%m-%d %H:%M:%S")
    )
    logger.addHandler(_archivo)


def registrar_error(contexto, error):
    """Guarda el error en errores.log, incluyendo la causa original (encadenamiento)."""
    causa = ""
    if error.__cause__ is not None:
        causa = f" | Causa: {type(error.__cause__).__name__}: {error.__cause__}"
    logger.error(f"{contexto} -> {type(error).__name__}: {error}{causa}")


def moneda(valor):
    """Formato colombiano: $1.234.567"""
    return "$" + f"{valor:,.0f}".replace(",", ".")


# =====================================================
