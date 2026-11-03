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
# 3. CLASE ABSTRACTA GENERAL: ENTIDAD
# =====================================================
class Entidad(ABC):
    """Base de todo objeto del sistema. No se puede instanciar directamente."""
    _prefijo = "ENT"
    _contadores = {}

    def __init__(self):
        n = Entidad._contadores.get(self._prefijo, 0) + 1
        Entidad._contadores[self._prefijo] = n
        self._id = f"{self._prefijo}-{n:03d}"

    @property
    def id(self):
        return self._id

    @abstractmethod
    def describir(self):
        """Cada clase hija debe describirse a sí misma."""

    def __str__(self):
        return self.describir()


# =====================================================
# 4. CLIENTE (encapsulación + validaciones)
# =====================================================
class Cliente(Entidad):
    _prefijo = "CLI"

    def __init__(self, documento, nombre, contacto):
        # Se asigna con self.x para que pase por el setter y se valide.
        self.documento = documento
        self.nombre = nombre
        self.contacto = contacto
        super().__init__()  # el ID solo se asigna si los datos fueron válidos

    @property
    def documento(self):
        return self.__documento

    @documento.setter
    def documento(self, valor):
        if not isinstance(valor, str) or not valor.strip().isdigit():
            raise ClienteInvalidoError("El documento debe contener solo números.")
        valor = valor.strip()
        if not 6 <= len(valor) <= 12:
            raise ClienteInvalidoError("El documento debe tener entre 6 y 12 dígitos.")
        self.__documento = valor

    @property
    def nombre(self):
        return self.__nombre

    @nombre.setter
    def nombre(self, valor):
        if not isinstance(valor, str):
            raise ClienteInvalidoError("El nombre debe ser texto.")
        valor = valor.strip()
        if len(valor) < 3 or not re.fullmatch(r"[A-Za-zÁÉÍÓÚáéíóúÑñÜü ]+", valor):
            raise ClienteInvalidoError(
                "El nombre debe tener mínimo 3 letras y no puede incluir números ni símbolos."
            )
        self.__nombre = valor

    @property
    def contacto(self):
        return self.__contacto

    @contacto.setter
    def contacto(self, valor):
        if not isinstance(valor, str):
            raise ClienteInvalidoError("El contacto debe ser texto.")
        valor = valor.strip()
        es_correo = re.fullmatch(r"[\w.+-]+@[\w-]+\.[\w.-]+", valor)
        es_celular = re.fullmatch(r"3\d{9}", valor)
        if not (es_correo or es_celular):
            raise ClienteInvalidoError(
                "El contacto debe ser un correo válido o un celular de 10 dígitos que empiece en 3."
            )
        self.__contacto = valor

    def describir(self):
        return (f"{self.id} | Documento: {self.documento} | "
                f"Nombre: {self.nombre} | Contacto: {self.contacto}")


# =====================================================
