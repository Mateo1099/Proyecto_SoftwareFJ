# Sistema de Gestión Software FJ

Proyecto de la Fase 4 del curso de Programación (213023A_2204), UNAD.
Es un sistema por consola, hecho en Python, para registrar clientes, crear servicios y reservarlos. Todo se guarda en listas en memoria, sin base de datos.

## Qué hace

- Registra clientes validando documento, nombre y contacto.
- Maneja tres tipos de servicio con costos distintos: sala, alquiler de equipo y asesoría.
- Crea reservas con fecha válida y evita que un servicio se reserve dos veces el mismo día.
- Guarda todos los errores en `errores.log` y sigue funcionando.
- Ejecuta una simulación automática de 20 operaciones, válidas e inválidas.

## Cómo ejecutarlo

Necesitas Python 3.8 o superior. No hay que instalar nada.

    python main.py          # simulación automática
    python main.py --menu   # simulación y luego menú interactivo

## Estructura de clases

    Entidad (abstracta)
    ├── Cliente
    ├── Servicio (abstracta)
    │   ├── ReservaSala
    │   ├── AlquilerEquipo
    │   └── Asesoria
    └── Reserva

    Sistema      -> guarda las listas y coordina las operaciones
    ErrorSistemaFJ
    ├── ClienteInvalidoError
    ├── ServicioInvalidoError
    └── ReservaInvalidaError

## Cómo se calcula el costo

Cada servicio sobreescribe `calcular_costo()`, y todos suman IVA del 19 % y aceptan un descuento opcional de hasta 50 %.

| Servicio | Fórmula antes de IVA |
|---|---|
| ReservaSala | costo base x horas, más $20.000 si la capacidad pasa de 10 personas |
| AlquilerEquipo | costo base x días, más un recargo según el equipo (Proyector, Portátil o Sonido) |
| Asesoria | costo base x horas, y 50 % más si el nivel es Avanzado |

## Manejo de errores

- Las excepciones propias heredan de `ErrorSistemaFJ`.
- Cada operación del sistema usa `try/except/else/finally`.
- Cuando un error tiene una causa original, se encadena con `raise ... from` y queda escrita en el log.
- Ejemplo de línea en `errores.log`:

      [2026-11-03 23:27:29] ERROR: crear_reserva -> ReservaInvalidaError: La fecha debe tener el formato DD/MM/AAAA. | Causa: ValueError: time data '31-12-2026' does not match format '%d/%m/%Y'

## Autor

Mateo Trujillo Estrada, Ingeniería de Sistemas, UNAD.