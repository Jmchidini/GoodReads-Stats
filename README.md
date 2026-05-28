# 📚 Goodreads Explorer

Visualización interactiva de tu historial de lectura exportado desde Goodreads. Permite explorar tus libros con zoom, filtros y drill-down por autor, género, año y más.

---

## ✨ Funcionalidades

- **Scatter plot interactivo** — Año de publicación vs. año de lectura, con zoom y pan
- **Colores por género** — Cada punto está coloreado según el shelf de Goodreads
- **Clic para explorar** — Hacé clic en cualquier barra para ver los libros de esa categoría
- **Filtros globales** — Por año de lectura, año de publicación, género y rating
- **Estadísticas completas**:
  - Top autores por cantidad y por rating promedio
  - Libros y páginas leídas por año y por mes
  - Curva acumulada de lectura
  - Distribución de ratings
  - Libros por género y por década de publicación
  - Rankings: libros más largos, 5 estrellas, últimos leídos

---

## 🚀 Cómo usar

### Opción A — Doble clic (Windows)
1. Descargá o cloná este repositorio
2. Hacé doble clic en `ejecutar_goodreads.bat`
3. Se abre automáticamente en el navegador

### Opción B — Terminal
```bash
pip install streamlit plotly pandas
streamlit run goodreads_explorer.py
```

---

## 📂 Exportar tus datos desde Goodreads

1. Entrá a [goodreads.com](https://www.goodreads.com)
2. **My Books** → **Import/Export**
3. Clic en **Export Library**
4. Guardá el archivo `goodreads_library_export.csv` en la misma carpeta que el script
5. Subilo desde la app al iniciarla

> ⚠️ El CSV contiene datos personales — está incluido en el `.gitignore` para que no se suba al repositorio por accidente.

---

## 🛠️ Requisitos

- Python 3.9 o superior
- Las dependencias se instalan automáticamente al ejecutar el `.bat`, o manualmente:

```bash
pip install streamlit plotly pandas
```

---

## 📁 Estructura del proyecto

```
goodreads-explorer/
├── goodreads_explorer.py   # App principal
├── ejecutar_goodreads.bat  # Lanzador para Windows
├── .gitignore              # Excluye el CSV y archivos temporales
└── README.md               # Este archivo
```
