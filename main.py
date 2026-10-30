import datetime
from abc import ABC, abstractmethod

# --- 1. CLASE CLIENTE ---
class Cliente:
    def __init__(self, documento, nombre, contacto):
        self.__documento = documento
        self.__nombre = nombre
        self.__contacto = contacto

    def get_documento(self):
        return self.__documento

    def get_nombre(self):
        return self.__nombre

    def get_contacto(self):
        return self.__contacto
    
    def __str__(self):
        return f"Documento: {self.__documento} | Nombre: {self.__nombre} | Contacto: {self.__contacto}"

# --- 2. CLASE PADRE ABSTRACTA (SERVICIO) ---
class Servicio(ABC):
    def __init__(self, nombre, costo_base):
        self.__nombre = nombre
        self.__costo_base = costo_base

    def get_nombre(self):
        return self.__nombre

    def get_costo_base(self):
        return self.__costo_base

    @abstractmethod
    def calcular_costo(self):
        pass

    def __str__(self):
        return f"Servicio: {self.__nombre} | Costo Base: ${self.__costo_base}"

# --- 3. CLASES HIJAS (SERVICIOS ESPECÍFICOS) ---
class ReservaSala(Servicio):
    def __init__(self, nombre, costo_base, capacidad):
        super().__init__(nombre, costo_base)
        self.__capacidad = capacidad

    def calcular_costo(self):
        costo = self.get_costo_base()
        if self.__capacidad > 10:
            costo = costo + 20000
        return costo

class AlquilerEquipo(Servicio):
    def __init__(self, nombre, costo_base, tipo_equipo):
        super().__init__(nombre, costo_base)
        self.__tipo_equipo = tipo_equipo

    def calcular_costo(self):
        costo = self.get_costo_base()
        if self.__tipo_equipo == "Proyector":
            costo = costo + 15000
        return costo

class Asesoria(Servicio):
    def __init__(self, nombre, costo_base, horas):
        super().__init__(nombre, costo_base)
        self.__horas = horas

    def calcular_costo(self):
        return self.get_costo_base() * self.__horas

# --- 4. CLASE RESERVA ---
class Reserva:
    def __init__(self, cliente, servicio, fecha):
        self.__cliente = cliente
        self.__servicio = servicio
        self.__fecha = fecha

    def get_cliente(self):
        return self.__cliente

    def get_servicio(self):
        return self.__servicio

    def get_fecha(self):
        return self.__fecha

    def __str__(self):
        return f"--- RESERVA ---\nFecha: {self.__fecha}\nCliente: {self.__cliente.get_nombre()}\n{self.__servicio.get_nombre()} - Total a pagar: ${self.__servicio.calcular_costo()}\n---------------"

# --- 5. CLASE SISTEMA (MOTOR Y EXCEPCIONES) ---
class Sistema:
    def __init__(self):
        self.__clientes = []
        self.__servicios_disponibles = [
            ReservaSala("Sala de Juntas", 50000, 15),
            AlquilerEquipo("Proyector Epson", 30000, "Proyector"),
            Asesoria("Asesoría Técnica de Software", 40000, 2)
        ]
        self.__reservas = []

    def registrar_error(self, mensaje):
        # Abre el archivo en modo "a" (append) para añadir errores sin borrar los anteriores
        with open("errores.log", "a", encoding="utf-8") as archivo:
            fecha_hora = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            archivo.write(f"[{fecha_hora}] ERROR: {mensaje}\n")

    def iniciar(self):
        while True:
            print("\n--- SISTEMA DE GESTIÓN SOFTWARE FJ ---")
            print("1. Registrar Cliente")
            print("2. Crear Reserva")
            print("3. Ver Reservas")
            print("4. Salir")
            
            try:
                opcion = int(input("Seleccione una opción numérica: "))
                
                if opcion == 1:
                    doc = input("Documento: ")
                    nom = input("Nombre completo: ")
                    cont = input("Contacto (Teléfono/Email): ")
                    nuevo_cliente = Cliente(doc, nom, cont)
                    self.__clientes.append(nuevo_cliente)
                    print("-> Cliente registrado con éxito.")
                    
                elif opcion == 2:
                    if not self.__clientes:
                        print("-> No hay clientes registrados. Registre un cliente primero.")
                        continue
                        
                    print("\nClientes disponibles:")
                    for i, c in enumerate(self.__clientes):
                        print(f"{i}. {c.get_nombre()} (ID: {c.get_documento()})")
                    indice_cliente = int(input("Seleccione el número del cliente: "))
                    cliente_seleccionado = self.__clientes[indice_cliente]
                    
                    print("\nServicios disponibles:")
                    for i, s in enumerate(self.__servicios_disponibles):
                        print(f"{i}. {s.get_nombre()} - Base: ${s.get_costo_base()}")
                    indice_servicio = int(input("Seleccione el número del servicio: "))
                    servicio_seleccionado = self.__servicios_disponibles[indice_servicio]
                    
                    fecha = input("Ingrese la fecha de reserva (Ej: DD/MM/AAAA): ")
                    
                    nueva_reserva = Reserva(cliente_seleccionado, servicio_seleccionado, fecha)
                    self.__reservas.append(nueva_reserva)
                    print("-> Reserva procesada con éxito.")
                    
                elif opcion == 3:
                    if not self.__reservas:
                        print("-> No hay reservas registradas en el sistema.")
                    else:
                        for r in self.__reservas:
                            print(r)
                            
                elif opcion == 4:
                    print("Saliendo del sistema...")
                    break
                else:
                    print("-> Opción no válida. Ingrese un número del 1 al 4.")
                    
            # --- MANEJO DE EXCEPCIONES REQUERIDO POR LA RÚBRICA ---
            except ValueError as e:
                print("-> Error crítico: Debe ingresar un número válido. Intente de nuevo.")
                self.registrar_error(f"ValueError - Entrada incorrecta. Detalle: {e}")
            
            except IndexError as e:
                print("-> Error crítico: El número seleccionado no existe en la lista. Intente de nuevo.")
                self.registrar_error(f"IndexError - Selección fuera de rango. Detalle: {e}")
            
            except Exception as e:
                print("-> Ocurrió un error inesperado en el sistema.")
                self.registrar_error(f"Exception general. Detalle: {e}")

# Ejecución del programa
if __name__ == "__main__":
    app = Sistema()
    app.iniciar()