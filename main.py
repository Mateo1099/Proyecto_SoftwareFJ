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
# 5. SERVICIO ABSTRACTO Y TRES HIJAS (polimorfismo)
# =====================================================
class Servicio(Entidad):
    """Clase abstracta: define qué es un servicio, pero no cómo se cobra."""
    _prefijo = "SRV"

    def __init__(self, nombre, costo_base):
        self.nombre = nombre
        self.costo_base = costo_base
        super().__init__()

    @property
    def nombre(self):
        return self.__nombre

    @nombre.setter
    def nombre(self, valor):
        if not isinstance(valor, str) or len(valor.strip()) < 3:
            raise ServicioInvalidoError("El nombre del servicio debe tener mínimo 3 caracteres.")
        self.__nombre = valor.strip()

    @property
    def costo_base(self):
        return self.__costo_base

    @costo_base.setter
    def costo_base(self, valor):
        if isinstance(valor, bool) or not isinstance(valor, (int, float)) or valor <= 0:
            raise ServicioInvalidoError("El costo base debe ser un número mayor que cero.")
        self.__costo_base = valor

    @staticmethod
    def _validar_entero(valor, minimo, maximo, campo):
        if isinstance(valor, bool) or not isinstance(valor, int) or not minimo <= valor <= maximo:
            raise ServicioInvalidoError(f"{campo} debe ser un entero entre {minimo} y {maximo}.")
        return valor

    def _aplicar_ajustes(self, subtotal, descuento):
        """Aplica descuento (0 a 0.5) e IVA. Lo usan todas las hijas."""
        if isinstance(descuento, bool) or not isinstance(descuento, (int, float)) \
                or not 0 <= descuento <= 0.5:
            raise ServicioInvalidoError("El descuento debe estar entre 0 y 0.5 (0% a 50%).")
        return round(subtotal * (1 - descuento) * (1 + IVA))

    @abstractmethod
    def calcular_costo(self, descuento=0.0):
        """Cada hija define su propia fórmula (sobreescritura)."""

    def describir(self):
        return f"{self.id} | {self.nombre} | Base: {moneda(self.costo_base)} | Costo estándar: {moneda(self.calcular_costo())}"


class ReservaSala(Servicio):
    """Costo base por hora. Salas de más de 10 personas tienen recargo fijo."""

    def __init__(self, nombre, costo_base, capacidad, horas):
        self.capacidad = self._validar_entero(capacidad, 1, 100, "La capacidad")
        self.horas = self._validar_entero(horas, 1, 12, "Las horas")
        super().__init__(nombre, costo_base)

    def calcular_costo(self, descuento=0.0):
        subtotal = self.costo_base * self.horas
        if self.capacidad > 10:
            subtotal += 20000
        return self._aplicar_ajustes(subtotal, descuento)


class AlquilerEquipo(Servicio):
    """Costo base por día. Cada tipo de equipo tiene un recargo distinto."""
    RECARGOS = {"Proyector": 15000, "Portátil": 10000, "Sonido": 20000}

    def __init__(self, nombre, costo_base, tipo_equipo, dias):
        if tipo_equipo not in self.RECARGOS:
            raise ServicioInvalidoError(
                f"Tipo de equipo no válido. Opciones: {', '.join(self.RECARGOS)}.")
        self.tipo_equipo = tipo_equipo
        self.dias = self._validar_entero(dias, 1, 30, "Los días")
        super().__init__(nombre, costo_base)

    def calcular_costo(self, descuento=0.0):
        subtotal = self.costo_base * self.dias + self.RECARGOS[self.tipo_equipo]
        return self._aplicar_ajustes(subtotal, descuento)


class Asesoria(Servicio):
    """Costo base por hora. El nivel Avanzado cuesta 50% más."""

    def __init__(self, nombre, costo_base, horas, nivel="Básico"):
        if nivel not in ("Básico", "Avanzado"):
            raise ServicioInvalidoError("El nivel debe ser 'Básico' o 'Avanzado'.")
        self.nivel = nivel
        self.horas = self._validar_entero(horas, 1, 40, "Las horas")
        super().__init__(nombre, costo_base)

    def calcular_costo(self, descuento=0.0):
        subtotal = self.costo_base * self.horas
        if self.nivel == "Avanzado":
            subtotal *= 1.5
        return self._aplicar_ajustes(subtotal, descuento)


CATALOGO_SERVICIOS = {"sala": ReservaSala, "equipo": AlquilerEquipo, "asesoria": Asesoria}


# =====================================================
