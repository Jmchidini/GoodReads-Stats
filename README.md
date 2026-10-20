# 📚 Goodreads Explorer

Aplicación local en Streamlit, pandas y Plotly para explorar un CSV de Goodreads.
Incluye español e inglés, filtros globales y cuatro pestañas: publicación frente
a lectura, autores y mapas, historial, géneros y rankings.

## Instalación y ejecución

Entorno de referencia: **Python 3.12 en Windows**. `requirements.txt` registra
versiones exactas de dependencias directas y transitivas.

Con Python 3.12 instalado, hacé doble clic en `goodreads.bat`. Usa `.venv` si
existe; de lo contrario busca Python. Instala las dependencias y abre Streamlit.
Se detiene con un mensaje si la versión o la instalación fallan.

Para instalar en un entorno aislado desde PowerShell:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run goodreads_explorer.py
```

Para detener la aplicación, presioná Ctrl+C en la terminal.

## Cargar tus datos

En Goodreads, entrá a **My Books → Import/Export → Export Library**. Descargá
el CSV y seleccionalo en la barra lateral. Puede estar en cualquier carpeta;
no se carga automáticamente por estar junto al script. Los CSV se excluyen de
Git porque contienen datos personales.

## Criterios de cálculo

- Solo se incluyen filas con `Exclusive Shelf` igual a `read`, si existe la columna.
- El año de publicación original tiene prioridad sobre el de la edición.
- Las etiquetas de `Bookshelves` se usan como géneros: un libro puede contar en varios.
- Cero significa sin puntuación: se excluye de todos los promedios, pero el libro
  sigue contando y sumando páginas. Sin puntuaciones se muestra «Sin puntuación».
- El ranking de autores por promedio exige dos libros puntuados dentro de los filtros.
- Los libros sin fecha cuentan en los totales, pero no en los gráficos temporales.
- Los ocho libros más largos se ordenan por páginas descendentes. Los últimos diez
  leídos y las tablas generales se ordenan por fecha descendente.
- País y género de autores provienen de archivos locales y pueden requerir revisión.

## Actualizar datos de autores

Desde la carpeta del proyecto, con acceso a Internet:

```powershell
.\.venv\Scripts\python.exe buscar_paises_autores.py "ruta\exportacion.csv"
.\.venv\Scripts\python.exe buscar_genero_autores.py "ruta\exportacion.csv"
```

El primer script consulta Wikipedia y guarda `locales/author_countries.json`.
El segundo consulta Wikidata y guarda `locales/author_genders.json` (`H`, `M`, `O`).
Reutilizan resultados existentes y priorizan sus `MANUAL_OVERRIDES`. Revisá los
resultados no encontrados que reportan. Reiniciá Streamlit después de actualizar
estos archivos para renovar la caché. La aplicación no ejecuta estas consultas.

## Traducciones

`idiomas.py` registra los idiomas admitidos. `locales/es.json` es la referencia.
Después de agregar una clave en español, ejecutá:

```powershell
.\.venv\Scripts\python.exe sincronizar_locales.py
```

Agrega claves faltantes a los archivos existentes de idiomas registrados, con el
prefijo `[TRADUCIR]`; completalas manualmente. Conserva traducciones existentes
y reporta claves obsoletas sin borrarlas. No modifica español ni datos de autores.
Usa `locales` junto al script, independientemente de la carpeta de ejecución.

Para agregar otro idioma, registralo en `LANGUAGES`, creá su JSON (puede empezar
como `{}`), sincronizá y completá las traducciones. La aplicación usa ese mismo
registro para el selector. Los países tienen traducción específica solo al inglés;
otros idiomas requieren completar esa parte.

## Pruebas

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Cubren promedios, orden de tablas, conservación de archivos del sincronizador y
la interfaz en ambos idiomas con un CSV sintético. No consultan servicios externos
ni requieren datos personales.

## Estructura

```text
goodreads_explorer.py       Interfaz, carga del CSV y gráficos
estadisticas.py            Promedios y orden de tablas
idiomas.py                 Registro compartido de idiomas
sincronizar_locales.py     Sincronización de traducciones
buscar_paises_autores.py   Actualización de países
buscar_genero_autores.py   Actualización de géneros de autores
goodreads.bat              Lanzador de Windows
requirements.txt          Versiones de las dependencias
locales/                  Traducciones y datos de autores
tests/                    Pruebas de regresión e integración
```
