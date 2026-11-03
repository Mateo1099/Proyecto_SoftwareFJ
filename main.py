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
# 6. RESERVA
# =====================================================
class Reserva(Entidad):
    _prefijo = "RES"

    def __init__(self, cliente, servicio, fecha_txt, descuento=0.0):
        if not isinstance(cliente, Cliente):
            raise ReservaInvalidaError("La reserva necesita un cliente válido.")
        if not isinstance(servicio, Servicio):
            raise ReservaInvalidaError("La reserva necesita un servicio válido.")
        fecha = self.parsear_fecha(fecha_txt)
        self.cliente = cliente
        self.servicio = servicio
        self.fecha = fecha
        self.total = servicio.calcular_costo(descuento)  # polimorfismo
        self.estado = "Confirmada"
        super().__init__()

    @staticmethod
    def parsear_fecha(fecha_txt):
        try:
            fecha = datetime.strptime(str(fecha_txt).strip(), "%d/%m/%Y").date()
        except ValueError as e:
            # ENCADENAMIENTO: el ValueError original queda como causa
            raise ReservaInvalidaError("La fecha debe tener el formato DD/MM/AAAA.") from e
        if fecha < datetime.now().date():
            raise ReservaInvalidaError("No se puede reservar en una fecha pasada.")
        return fecha

    def describir(self):
        return (f"{self.id} | {self.fecha:%d/%m/%Y} | Cliente: {self.cliente.nombre} | "
                f"{self.servicio.nombre} | Total: {moneda(self.total)} | {self.estado}")


# =====================================================
# 7. SISTEMA (listas en memoria + manejo de excepciones)
# =====================================================
class Sistema:
    def __init__(self):
        self.__clientes = []
        self.__servicios = []
        self.__reservas = []
        self.__stats = {"exitosas": 0, "fallidas": 0}

    # ---------- utilidades ----------
    def _fallo(self, contexto, error):
        """Muestra el error, lo guarda en errores.log y lo cuenta. No detiene el programa."""
        self.__stats["fallidas"] += 1
        print(f"   [X] {contexto}: {error}")
        registrar_error(contexto, error)

    def _exito(self, mensaje):
        self.__stats["exitosas"] += 1
        print(f"   [OK] {mensaje}")

    def buscar_cliente(self, documento):
        for c in self.__clientes:
            if c.documento == str(documento).strip():
                return c
        raise ClienteInvalidoError(f"No existe un cliente con documento {documento}.")

    # ---------- operaciones ----------
    def registrar_cliente(self, documento, nombre, contacto):
        cliente = None
        try:
            for c in self.__clientes:
                if c.documento == str(documento).strip():
                    raise ClienteInvalidoError(f"Ya existe un cliente con documento {documento}.")
            cliente = Cliente(documento, nombre, contacto)
        except ErrorSistemaFJ as e:
            self._fallo("registrar_cliente", e)
        except Exception as e:  # error inesperado: el sistema sigue vivo
            self._fallo("registrar_cliente (inesperado)", e)
        else:  # solo se ejecuta si NO hubo excepción
            self.__clientes.append(cliente)
            self._exito(f"Cliente registrado: {cliente.nombre} ({cliente.id})")
        finally:  # se ejecuta SIEMPRE
            print("   (operación 'registrar_cliente' finalizada)")
        return cliente

    def crear_servicio(self, tipo, *parametros):
        servicio = None
        try:
            try:
                clase = CATALOGO_SERVICIOS[str(tipo).lower()]
            except KeyError as e:
                raise ServicioInvalidoError(f"Tipo de servicio desconocido: '{tipo}'.") from e
            try:
                servicio = clase(*parametros)
            except TypeError as e:
                raise ServicioInvalidoError("Faltan o sobran parámetros para este servicio.") from e
        except ErrorSistemaFJ as e:
            self._fallo("crear_servicio", e)
        except Exception as e:
            self._fallo("crear_servicio (inesperado)", e)
        else:
            self.__servicios.append(servicio)
            self._exito(f"Servicio creado: {servicio.nombre} ({servicio.id})")
        finally:
            print("   (operación 'crear_servicio' finalizada)")
        return servicio

    def crear_reserva(self, documento, indice_servicio, fecha_txt, descuento=0.0):
        reserva = None
        try:
            cliente = self.buscar_cliente(documento)
            try:
                if indice_servicio < 0:
                    raise IndexError("índice negativo")
                servicio = self.__servicios[indice_servicio]
            except IndexError as e:
                raise ReservaInvalidaError("El servicio seleccionado no existe.") from e
            fecha = Reserva.parsear_fecha(fecha_txt)
            for r in self.__reservas:
                if r.servicio is servicio and r.fecha == fecha:
                    raise ReservaInvalidaError("Ese servicio ya está reservado en esa fecha.")
            reserva = Reserva(cliente, servicio, fecha_txt, descuento)
        except ErrorSistemaFJ as e:
            reserva = None
            self._fallo("crear_reserva", e)
        except Exception as e:
            reserva = None
            self._fallo("crear_reserva (inesperado)", e)
        else:
            self.__reservas.append(reserva)
            self._exito(f"Reserva confirmada: {reserva.id} por {moneda(reserva.total)}")
        finally:
            print("   (operación 'crear_reserva' finalizada)")
        return reserva

    # ---------- consultas ----------
    def listar(self, titulo, elementos):
        print(f"\n--- {titulo} ({len(elementos)}) ---")
        if not elementos:
            print("   (sin registros)")
        for e in elementos:
            print("  ", e)

    def mostrar_clientes(self):
        self.listar("CLIENTES", self.__clientes)

    def mostrar_servicios(self):
        self.listar("SERVICIOS", self.__servicios)

    def mostrar_reservas(self):
        self.listar("RESERVAS", self.__reservas)

    def resumen(self):
        print("\n=== RESUMEN ===")
        print(f"Clientes: {len(self.__clientes)} | Servicios: {len(self.__servicios)} | "
              f"Reservas: {len(self.__reservas)}")
        print(f"Operaciones exitosas: {self.__stats['exitosas']} | "
              f"Operaciones fallidas (registradas en errores.log): {self.__stats['fallidas']}")

    # ---------- simulación automática ----------
    def ejecutar_simulacion(self):
        hoy = datetime.now()
        f1 = (hoy + timedelta(days=5)).strftime("%d/%m/%Y")
        f2 = (hoy + timedelta(days=6)).strftime("%d/%m/%Y")
        f3 = (hoy + timedelta(days=7)).strftime("%d/%m/%Y")
        ayer = (hoy - timedelta(days=1)).strftime("%d/%m/%Y")

        pasos = [
            ("1. Cliente válido (celular)", self.registrar_cliente, ("1094123456", "Ana María Gómez", "3105551234")),
            ("2. Cliente válido (correo)", self.registrar_cliente, ("1088765432", "Carlos Ruiz", "carlos@correo.com")),
            ("3. Cliente con documento inválido", self.registrar_cliente, ("ABC123", "Pedro Pérez", "3115559876")),
            ("4. Cliente con nombre inválido", self.registrar_cliente, ("1098111222", "J0hn 123", "3115559876")),
            ("5. Cliente con contacto inválido", self.registrar_cliente, ("1098333444", "Laura Díaz", "12345")),
            ("6. Cliente duplicado", self.registrar_cliente, ("1094123456", "Ana María Gómez", "3105551234")),
            ("7. Servicio sala válido", self.crear_servicio, ("sala", "Sala de Juntas", 50000, 15, 3)),
            ("8. Servicio equipo válido", self.crear_servicio, ("equipo", "Proyector Epson", 30000, "Proyector", 2)),
            ("9. Servicio asesoría válido", self.crear_servicio, ("asesoria", "Asesoría de Software", 40000, 4, "Avanzado")),
            ("10. Servicio con costo negativo", self.crear_servicio, ("sala", "Sala Pequeña", -5000, 5, 2)),
            ("11. Servicio de tipo desconocido", self.crear_servicio, ("hotel", "Suite", 100000)),
            ("12. Servicio con parámetros incompletos", self.crear_servicio, ("equipo", "Portátil HP", 20000)),
            ("13. Reserva exitosa", self.crear_reserva, ("1094123456", 0, f1)),
            ("14. Reserva exitosa con descuento", self.crear_reserva, ("1088765432", 2, f2, 0.10)),
            ("15. Reserva con cliente inexistente", self.crear_reserva, ("9999999", 0, f3)),
            ("16. Reserva con fecha mal escrita", self.crear_reserva, ("1094123456", 1, "31-12-2026")),
            ("17. Reserva con fecha pasada", self.crear_reserva, ("1094123456", 1, ayer)),
            ("18. Reserva con servicio inexistente", self.crear_reserva, ("1094123456", 9, f3)),
            ("19. Reserva duplicada (mismo servicio y fecha)", self.crear_reserva, ("1088765432", 0, f1)),
            ("20. Reserva exitosa de equipo", self.crear_reserva, ("1088765432", 1, f3)),
        ]

        print("=" * 60)
        print(" SIMULACIÓN AUTOMÁTICA - SISTEMA DE GESTIÓN SOFTWARE FJ")
        print("=" * 60)
        for titulo, funcion, argumentos in pasos:
            print(f"\n>> {titulo}")
            funcion(*argumentos)  # cada operación maneja sus propios errores

        self.mostrar_clientes()
        self.mostrar_servicios()
        self.mostrar_reservas()
        self.resumen()

    # ---------- menú interactivo ----------
    def menu(self):
        opciones = """
--- SISTEMA DE GESTIÓN SOFTWARE FJ ---
1. Registrar cliente
2. Crear servicio
3. Crear reserva
4. Ver clientes
5. Ver servicios
6. Ver reservas
7. Salir"""
        while True:
            print(opciones)
            try:
                opcion = int(input("Seleccione una opción: "))
                if opcion == 1:
                    self.registrar_cliente(input("Documento: "), input("Nombre completo: "),
                                           input("Contacto (celular o correo): "))
                elif opcion == 2:
                    self._menu_servicio()
                elif opcion == 3:
                    self.mostrar_servicios()
                    doc = input("Documento del cliente: ")
                    indice = int(input("Número del servicio: ")) - 1
                    fecha = input("Fecha (DD/MM/AAAA): ")
                    self.crear_reserva(doc, indice, fecha)
                elif opcion == 4:
                    self.mostrar_clientes()
                elif opcion == 5:
                    self.mostrar_servicios()
                elif opcion == 6:
                    self.mostrar_reservas()
                elif opcion == 7:
                    print("Saliendo del sistema...")
                    break
                else:
                    print("-> Opción no válida. Ingrese un número del 1 al 7.")
            except ValueError as e:
                print("-> Debe ingresar un número válido.")
                registrar_error("menu", e)
            except (EOFError, KeyboardInterrupt):
                print("\nSaliendo del sistema...")
                break
            except Exception as e:
                print("-> Ocurrió un error inesperado. El sistema continúa.")
                registrar_error("menu (inesperado)", e)

    def _menu_servicio(self):
        print("Tipos: sala | equipo | asesoria")
        tipo = input("Tipo de servicio: ").strip().lower()
        nombre = input("Nombre del servicio: ")
        try:
            costo = float(input("Costo base: "))
            if tipo == "sala":
                params = (nombre, costo, int(input("Capacidad: ")), int(input("Horas: ")))
            elif tipo == "equipo":
                params = (nombre, costo, input("Tipo (Proyector/Portátil/Sonido): "), int(input("Días: ")))
            elif tipo == "asesoria":
                params = (nombre, costo, int(input("Horas: ")), input("Nivel (Básico/Avanzado): "))
            else:
                params = (nombre, costo)
        except ValueError as e:
            print("-> Dato numérico no válido.")
            registrar_error("menu_servicio", e)
            return
        self.crear_servicio(tipo, *params)


# =====================================================
# 8. PUNTO DE ENTRADA
# =====================================================
if __name__ == "__main__":
    app = Sistema()
    app.ejecutar_simulacion()
    if "--menu" in sys.argv:
        app.menu()