from datetime import datetime
import json
import os
import shutil

class Grafo:
    def __init__(self):
        self.nodos = {}
        self.adyacencia = {}

    def agregar_nodo(self, id_nodo, datos=None):
        if id_nodo not in self.nodos:
            self.nodos[id_nodo] = datos or {}
            self.adyacencia[id_nodo] = []
            return True
        return False

    def agregar_arista(self, origen, destino, bidireccional=False):
        if origen not in self.adyacencia:
            self.agregar_nodo(origen)
        if destino not in self.adyacencia:
            self.agregar_nodo(destino)
        if destino not in self.adyacencia[origen]:
            self.adyacencia[origen].append(destino)
        if bidireccional and origen not in self.adyacencia[destino]:
            self.adyacencia[destino].append(origen)

    def obtener_nodo(self, id_nodo):
        return self.nodos.get(id_nodo)

    def obtener_vecinos(self, id_nodo):
        return self.adyacencia.get(id_nodo, [])

    def dfs(self, inicio, objetivo=None, visitado=None):
        if visitado is None:
            visitado = set()
        visitado.add(inicio)
        resultados = []
        datos = self.nodos.get(inicio, {})
        if not objetivo or objetivo(datos, inicio):
            resultados.append((inicio, datos))
        for vecino in self.adyacencia.get(inicio, []):
            if vecino not in visitado:
                resultados.extend(self.dfs(vecino, objetivo, visitado))
        return resultados

    def bfs(self, inicio, objetivo=None):
        visitado, cola, resultados = set(), [inicio], []
        while cola:
            nodo = cola.pop(0)
            if nodo not in visitado:
                visitado.add(nodo)
                datos = self.nodos.get(nodo, {})
                if not objetivo or objetivo(datos, nodo):
                    resultados.append((nodo, datos))
                cola.extend(v for v in self.adyacencia.get(nodo, []) if v not in visitado)
        return resultados

class SistemaAlertas:
    def __init__(self):
        self.grafo = Grafo()
        self.archivo_datos = "sistema_alertas.json"
        self.datos = self._cargar_datos()
        self.user_id = None

        self.tipos_alerta = {
            'emergency': 'Emergencia',
            'crime': 'Crimen/Seguridad',
            'accident': 'Accidente',
            'traffic': 'Tráfico'
        }

        self.regiones = [
            'Bocas del Toro', 'Chiriquí', 'Coclé', 'Colón', 'Darién',
            'Herrera', 'Los Santos', 'Panamá', 'Panamá Oeste', 'Veraguas',
            'Comarca Guna Yala', 'Comarca Emberá-Wounaan', 'Comarca Ngäbe-Buglé',
            'Comarca Madugandí', 'Comarca Wargandí'
        ]
        self._inicializar_grafo()

    def _cargar_datos(self):
        if os.path.exists(self.archivo_datos):
            try:
                with open(self.archivo_datos, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return {"usuarios": [], "alertas": [], "conexiones": []}

    def _guardar_datos(self):
        try:
            if os.path.exists(self.archivo_datos):
                shutil.copy(self.archivo_datos, self.archivo_datos + ".bak")
            with open(self.archivo_datos, 'w', encoding='utf-8') as f:
                json.dump(self.datos, f, ensure_ascii=False, indent=2, default=str)
            return True
        except:
            return False

    def _inicializar_grafo(self):
        self.grafo.agregar_nodo("SISTEMA", {"tipo": "sistema"})
        # Agregar nodos tipo alerta y conexiones
        for tipo, nombre in self.tipos_alerta.items():
            nodo_id = f"TIPO_{tipo.upper()}"
            self.grafo.agregar_nodo(nodo_id, {"tipo": "categoria", "nombre": nombre})
            self.grafo.agregar_arista("SISTEMA", nodo_id)
        # Agregar nodos región y conexiones
        for region in self.regiones:
            nodo_id = f"REGION_{region.upper()}"
            self.grafo.agregar_nodo(nodo_id, {"tipo": "region", "nombre": region})
            self.grafo.agregar_arista("SISTEMA", nodo_id)
        # Agregar nodos alerta activos
        for alerta in self.datos["alertas"]:
            if alerta.get("activa", True):
                self.grafo.agregar_nodo(alerta["id"], alerta)
        # Agregar conexiones (aristas)
        for conexion in self.datos["conexiones"]:
            bidireccional = conexion.get("bidireccional", False)
            # Forzar bidireccionalidad en conexiones alerta_categoria y alerta_region para que DFS funcione bien
            if conexion.get("tipo") in ("alerta_categoria", "alerta_region"):
                bidireccional = True
            self.grafo.agregar_arista(conexion["origen"], conexion["destino"], bidireccional)

    def _input_numero(self, mensaje, minimo, maximo):
        while True:
            entrada = input(mensaje)
            if entrada.isdigit():
                num = int(entrada)
                if minimo <= num <= maximo:
                    return num
            print(f"⚠ Ingrese un número válido entre {minimo} y {maximo}")

    def _seleccionar_opcion(self, lista, mensaje):
        for i, item in enumerate(lista, 1):
            print(f"{i}. {item}")
        opcion = self._input_numero(mensaje, 1, len(lista))
        return lista[opcion - 1]

    def registrar_usuario(self):
        print("\n=== REGISTRO ===")
        nombre = input("Nombre: ")
        region = self._seleccionar_opcion(self.regiones, "Región: ")
        user_id = f"USER_{len(self.datos['usuarios']) + 1}"
        usuario = {"id": user_id, "nombre": nombre, "region": region, "created_at": datetime.now().isoformat()}
        self.grafo.agregar_nodo(user_id, {"tipo": "usuario", "nombre": nombre, "region": region})
        self.grafo.agregar_arista(user_id, f"REGION_{region.upper()}", True)
        self.datos["usuarios"].append(usuario)
        self.datos["conexiones"].append({"origen": user_id, "destino": f"REGION_{region.upper()}", "bidireccional": True, "tipo": "usuario_region"})
        if self._guardar_datos():
            print(f"Usuario registrado: {user_id}")
            self.user_id = user_id

    def crear_alerta(self):
        if not self.user_id:
            print("Debe registrarse primero")
            return
        print("\n=== NUEVA ALERTA ===")
        tipo = self._seleccionar_opcion(list(self.tipos_alerta.keys()), "Tipo: ")
        descripcion = input("Descripción: ")
        ubicacion = input("Ubicación: ")
        region = self._seleccionar_opcion(self.regiones, "Región: ")
        alerta_id = f"ALERTA_{tipo.upper()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        alerta = {
            "id": alerta_id,
            "descripcion": descripcion,
            "ubicacion": ubicacion,
            "region": region,
            "tipo": "alerta",
            "categoria": tipo,
            "user_id": self.user_id,
            "created_at": datetime.now().isoformat(),
            "activa": True
        }
        self.grafo.agregar_nodo(alerta_id, alerta)
        # Aquí el cambio: aristas bidireccionales para que DFS encuentre alertas desde tipo
        self.grafo.agregar_arista(alerta_id, f"TIPO_{tipo.upper()}", bidireccional=True)
        self.grafo.agregar_arista(alerta_id, f"REGION_{region.upper()}", bidireccional=True)
        self.grafo.agregar_arista(self.user_id, alerta_id)
        self.datos["alertas"].append(alerta)
        self.datos["conexiones"].extend([
            {"origen": alerta_id, "destino": f"TIPO_{tipo.upper()}", "tipo": "alerta_categoria"},
            {"origen": alerta_id, "destino": f"REGION_{region.upper()}", "tipo": "alerta_region"},
            {"origen": self.user_id, "destino": alerta_id, "tipo": "usuario_alerta"}
        ])
        if self._guardar_datos():
            print(f"Alerta creada: {alerta_id}")

    def buscar_alertas(self):
        print("\n=== BUSCAR ALERTAS ===")
        print("1. Por tipo (DFS)\n2. Por región (BFS)\n3. Mis alertas")
        opcion = self._input_numero("Opción: ", 1, 3)
        resultados = []
        if opcion == 1:
            tipo = self._seleccionar_opcion(list(self.tipos_alerta.keys()), "Tipo: ")
            resultados = self.grafo.dfs(
                f"TIPO_{tipo.upper()}",
                lambda d, _: d.get('tipo') == 'alerta' and d.get('activa') and d.get('categoria') == tipo
            )
        elif opcion == 2:
            region = self._seleccionar_opcion(self.regiones, "Región: ")
            resultados = self.grafo.bfs(
                f"REGION_{region.upper()}",
                lambda d, _: d.get('tipo') == 'alerta' and d.get('activa') and d.get('region') == region
            )
        elif opcion == 3:
            if not self.user_id:
                print("Debe registrarse primero")
                return
            for vecino in self.grafo.obtener_vecinos(self.user_id):
                datos = self.grafo.obtener_nodo(vecino)
                if datos and datos.get('tipo') == 'alerta':
                    resultados.append((vecino, datos))
        if resultados:
            print(f"\n=== {len(resultados)} ALERTAS ENCONTRADAS ===")
            for i, (nodo_id, datos) in enumerate(resultados, 1):
                print(f"\n{i}. {nodo_id}")
                print(f"   Descripción: {datos.get('descripcion', 'N/A')}")
                print(f"   Ubicación: {datos.get('ubicacion', 'N/A')}")
                print(f"   Región: {datos.get('region', 'N/A')}")
                print(f"   Fecha: {datos.get('created_at', 'N/A')}")
        else:
            print("No se encontraron alertas")

    def mostrar_estadisticas(self):
        print("\n=== ESTADÍSTICAS ===")
        print(f"Nodos: {len(self.grafo.nodos)}")
        print(f"Aristas: {sum(len(v) for v in self.grafo.adyacencia.values())}")
        print(f"Usuarios: {len(self.datos['usuarios'])}")
        print(f"Alertas activas: {len([a for a in self.datos['alertas'] if a.get('activa')])}")
        for tipo, nombre in self.tipos_alerta.items():
            count = sum(1 for a in self.datos['alertas'] if a.get('categoria') == tipo and a.get('activa'))
            print(f"{nombre}: {count}")

def main():
    sistema = SistemaAlertas()
    while True:
        print("\n" + "="*40)
        print("SISTEMA DE ALERTAS PANAMÁ")
        print("="*40)
        print("1. Registrar usuario.\n2. Crear alerta.\n3. Buscar alertas\n4. Estadísticas\n5. Salir.")
        opcion = sistema._input_numero("\nOpción: ", 1, 5)
        if opcion == 1:
            sistema.registrar_usuario()
        elif opcion == 2:
            sistema.crear_alerta()
        elif opcion == 3:
            sistema.buscar_alertas()
        elif opcion == 4:
            sistema.mostrar_estadisticas()
        elif opcion == 5:
            print("¡Hasta luego!")
            break

if __name__ == "__main__":
    main()
