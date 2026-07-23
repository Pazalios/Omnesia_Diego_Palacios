# Omnesia_Diego_Palacios

Proyecto para leer documentos de una carpeta de entrada, agruparlos en expedientes y generar un informe con la salida organizada en carpetas.

## Version de Python

Se necesita Python 3.8 o superior.

## Tests

Este repositorio no usa una suite formal de `pytest`. Los tests actuales son scripts ejecutables que usan el contenido de `dataset/inbox`.

Para correr el test por defecto:

```bash
python3 -m tests.run_sorter_default_test
```

Para comprobar solo la lectura de documentos del inbox:

```bash
python3 -m tests.read_documents
```

Para comprobar la extracción de expedientes:

```bash
python3 -m tests.extract_expedientes
```

Ambos comandos usan los datos de ejemplo incluidos en `dataset/inbox`.

## Ejecucion del proyecto

El punto de entrada principal esta en `src/inbox_sorter/main.py`.

```bash
python3 -m src.inbox_sorter.main
```

Al ejecutarlo sin parametros, usa estas rutas por defecto:

- Entrada: `dataset/inbox`
- Salida: `test_output`

Tambien puedes indicar rutas manualmente:

```bash
python3 -m src.inbox_sorter.main <ruta/al/inbox> <ruta/al/output>
```

Si solo indicas la ruta de entrada, la salida se generara en `test_output`.

## Que hace

El proceso lee los documentos `.txt` del inbox, extrae sus campos, agrupa los archivos en expedientes y genera un informe con:

- expedientes completos
- expedientes incompletos
- archivos que requieren atencion
- archivos renombrados
- archivos no procesables

Tambien copia los documentos a una estructura de salida separada por estado.

## Estructura del proyecto

```text
src/inbox_sorter/
	expediente.py   # Modelo de expediente y validaciones
	main.py         # Punto de entrada de la aplicacion
	utils.py        # Lectura, parseo, agrupacion y generacion del informe

dataset/inbox/    # Documentos de ejemplo de entrada
tests/            # Scripts de comprobacion manual
```

## Dependencias

El proyecto usa solo la biblioteca estandar de Python. El archivo `requirements.txt` esta vacio porque no hay dependencias externas declaradas.


## Notas

- El script principal pide confirmacion antes de procesar rutas externas.
- La carpeta de salida se crea automaticamente si no existe.
- Los documentos deben ser archivos `.txt` para ser procesados.
- Se corrigen los nombres de los archivos que no coincidan con el interior
- Los archivos con errores se ponen en una carpeta aparte "necesitan atención", en el informe se puede ver qué sucede.
- Los archivos duplicados se ponen en una carpeta de "archivos duplicados" dentro de cada expediente.
