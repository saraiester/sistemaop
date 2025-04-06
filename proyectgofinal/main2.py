import sys
from typing import List
from tabulate import tabulate

class Proceso:
    def __init__(self, id_proceso: str, tiempo_llegada: int, tiempo_ejecucion: int):
        self.id = id_proceso
        self.ti = tiempo_llegada      # Tiempo de llegada
        self.t = tiempo_ejecucion     # Tiempo de ejecución
        self.tf = 0                   # Tiempo de finalización
        self.T = 0                    # Tiempo de retorno (T = tf - ti)
        self.E = 0                    # Tiempo de espera (E = T - t)
        self.I = 0.0                  # Índice de penalización (I = t/T)
        self.tiempo_restante = tiempo_ejecucion  # Para Round Robin

def cargar_procesos(archivo: str = "datos.txt") -> List[Proceso]:
    """
    Carga procesos desde archivo .txt con formatos:
    - A (2, 1)
    - B,6,6
    - C 5 3
    """
    procesos = []
    try:
        with open(archivo, 'r') as file:
            for linea in file:
                linea = linea.strip()
                if not linea or linea.startswith('#'):
                    continue
                
                # Manejar múltiples formatos
                if '(' in linea:  # Formato: A (2, 1)
                    partes = linea.replace('(', ' ').replace(')', ' ').replace(',', ' ').split()
                elif ',' in linea:  # Formato: A,2,1
                    partes = linea.split(',')
                else:  # Formato: A 2 1
                    partes = linea.split()
                
                if len(partes) == 3:
                    try:
                        id_proc = partes[0].strip()
                        ti = int(partes[1])
                        t = int(partes[2])
                        procesos.append(Proceso(id_proc, ti, t))
                    except ValueError:
                        print(f"¡Advertencia! Formato incorrecto en línea: {linea}")
    
    except FileNotFoundError:
        print(f"\nERROR: No se encontró el archivo '{archivo}'")
        print("Por favor verifique:")
        print("1. Que el archivo existe en esta ubicación")
        print("2. Que el nombre y extensión son correctos")
        print("3. Ejemplo de formato válido:")
        print("   A (2, 1)  o  A,2,1  o  A 2 1")
        sys.exit(1)
    except Exception as e:
        print(f"\nERROR inesperado: {e}")
        sys.exit(1)
    
    if not procesos:
        print("\nERROR: El archivo no contiene datos válidos")
        print("Formato esperado (3 variantes aceptadas):")
        print("A (2, 1)  |  A,2,1  |  A 2 1")
        sys.exit(1)
        
    print(f"\n✓ Se cargaron {len(procesos)} procesos desde '{archivo}'")
    return procesos

def mostrar_resultados(titulo: str, procesos: List[Proceso]):
    """Muestra resultados en formato de tabla con promedios"""
    tabla = []
    for proc in sorted(procesos, key=lambda x: x.id):
        tabla.append([
            proc.id,
            proc.ti,
            proc.t,
            proc.tf,
            proc.T,
            proc.E,
            f"{proc.I:.4f}" if proc.T != 0 else "N/A"
        ])
    
    # Calcular promedios excluyendo divisiones por cero
    tiempos_T = [p.T for p in procesos]
    tiempos_E = [p.E for p in procesos]
    indices_I = [p.I for p in procesos if p.T != 0]
    
    avg_T = sum(tiempos_T)/len(tiempos_T) if tiempos_T else 0
    avg_E = sum(tiempos_E)/len(tiempos_E) if tiempos_E else 0
    avg_I = sum(indices_I)/len(indices_I) if indices_I else 0
    
    print(f"\n{'='*60}")
    print(titulo.center(60))
    print('='*60)
    print(tabulate(
        tabla,
        headers=["Proceso", "ti", "t", "tf", "T", "E", "I"],
        tablefmt="grid",
        stralign="center",
        numalign="center"
    ))
    print(f"\nPromedios: T={avg_T:.2f} | E={avg_E:.2f} | I={avg_I:.4f}")
    print('='*60)

def fifo(procesos: List[Proceso]) -> List[Proceso]:
    """Algoritmo First-In First-Out (FIFO)"""
    resultados = [Proceso(p.id, p.ti, p.t) for p in procesos]  # Copia
    reloj = 0
    completados = 0
    
    while completados < len(procesos):
        # Buscar próximo proceso a ejecutar
        proceso_actual = None
        for proc in resultados:
            if not proc.tf and proc.ti <= reloj:
                proceso_actual = proc
                break  # FIFO: toma el primero que encuentre
        
        if not proceso_actual:
            # Avanzar reloj al próximo tiempo de llegada
            reloj = min(p.ti for p in resultados if not p.tf)
            continue
        
        # Ejecutar proceso
        proceso_actual.tf = reloj + proceso_actual.t
        proceso_actual.T = proceso_actual.tf - proceso_actual.ti
        proceso_actual.E = proceso_actual.T - proceso_actual.t
        proceso_actual.I = proceso_actual.t / proceso_actual.T if proceso_actual.T else 0
        
        reloj = proceso_actual.tf
        completados += 1
    
    return resultados

def round_robin(procesos: List[Proceso], quantum: int) -> List[Proceso]:
    """Algoritmo Round Robin con quantum especificado"""
    resultados = [Proceso(p.id, p.ti, p.t) for p in procesos]  # Copia
    tiempos_restantes = [p.t for p in resultados]
    reloj = 0
    completados = 0
    cola = []
    indice = 0  # Para recorrer procesos
    
    while completados < len(procesos):
        # Añadir procesos que han llegado
        while indice < len(resultados) and resultados[indice].ti <= reloj:
            if tiempos_restantes[indice] > 0:
                cola.append(indice)
            indice += 1
        
        if not cola:
            reloj += 1
            continue
        
        # Tomar próximo proceso de la cola
        actual = cola.pop(0)
        tiempo_ejecucion = min(quantum, tiempos_restantes[actual])
        
        # Ejecutar proceso
        tiempos_restantes[actual] -= tiempo_ejecucion
        reloj += tiempo_ejecucion
        
        # Si terminó el proceso
        if tiempos_restantes[actual] == 0:
            resultados[actual].tf = reloj
            resultados[actual].T = resultados[actual].tf - resultados[actual].ti
            resultados[actual].E = resultados[actual].T - resultados[actual].t
            resultados[actual].I = resultados[actual].t / resultados[actual].T if resultados[actual].T else 0
            completados += 1
        else:
            # Reingresar a la cola si no terminó
            cola.append(actual)
    
    return resultados

def lifo(procesos: List[Proceso]) -> List[Proceso]:
    """Algoritmo Last-In First-Out (LIFO)"""
    resultados = [Proceso(p.id, p.ti, p.t) for p in procesos]  # Copia
    reloj = 0
    completados = 0
    
    while completados < len(procesos):
        # Buscar último proceso disponible
        proceso_actual = None
        for proc in reversed(resultados):
            if not proc.tf and proc.ti <= reloj:
                proceso_actual = proc
                break  # LIFO: toma el último disponible
        
        if not proceso_actual:
            # Avanzar reloj al próximo tiempo de llegada
            reloj = min(p.ti for p in resultados if not p.tf)
            continue
        
        # Ejecutar proceso
        proceso_actual.tf = reloj + proceso_actual.t
        proceso_actual.T = proceso_actual.tf - proceso_actual.ti
        proceso_actual.E = proceso_actual.T - proceso_actual.t
        proceso_actual.I = proceso_actual.t / proceso_actual.T if proceso_actual.T else 0
        
        reloj = proceso_actual.tf
        completados += 1
    
    return resultados

def main():
    print("\n" + "="*60)
    print(" SIMULADOR DE PLANIFICACIÓN DE PROCESOS ".center(60, '='))
    print("="*60)
    
    # Solicitar nombre de archivo
    nombre_archivo = input("\nIngrese el nombre del archivo de datos (ej: datos.txt): ").strip()
    if not nombre_archivo:
        nombre_archivo = "datos.txt"
    
    # Cargar procesos
    procesos = cargar_procesos(nombre_archivo)
    
    # Solicitar quantum para Round Robin
    quantum = int(input("\nIngrese el quantum para Round Robin (ej: 3): "))
    
    # Ejecutar algoritmos
    print("\nEjecutando Round Robin...")
    rr_resultados = round_robin(procesos, quantum)
    mostrar_resultados("RESULTADOS ROUND ROBIN", rr_resultados)
    
    print("\nEjecutando FIFO...")
    fifo_resultados = fifo(procesos)
    mostrar_resultados("RESULTADOS FIFO", fifo_resultados)
    
    print("\nEjecutando LIFO...")
    lifo_resultados = lifo(procesos)
    mostrar_resultados("RESULTADOS LIFO", lifo_resultados)

if __name__ == "__main__":
    main()