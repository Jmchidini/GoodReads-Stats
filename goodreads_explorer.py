"""
Goodreads Explorer — Streamlit App
Cargá tu CSV exportado desde Goodreads y explorá tu historial de lectura.

Instalación:
  pip install streamlit plotly pandas

Ejecución:
  streamlit run goodreads_explorer.py
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import json
import os

# ── Sistema de traducciones ───────────────────────────────────────────────────
LANGUAGES = {"Español": "es", "English": "en"}

@st.cache_data
def load_locale(lang_code: str) -> dict:
    path = os.path.join(os.path.dirname(__file__), "locales", f"{lang_code}.json")
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def t(key: str) -> str:
    """Retorna el string traducido para la clave dada."""
    return st.session_state.get("locale", {}).get(key, key)

@st.cache_data
def load_author_countries() -> dict:
    """Carga el cache de país por autor generado por buscar_paises_autores.py."""
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "locales", "author_countries.json")
    if not os.path.exists(path):
        return {}
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

# Nombre de país (español) -> código ISO-3 para el mapa coroplético
COUNTRY_ISO3 = {
    "Estados Unidos": "USA", "Reino Unido": "GBR", "Francia": "FRA",
    "Japón": "JPN", "Alemania": "DEU", "Rusia": "RUS", "China": "CHN",
    "Argentina": "ARG", "España": "ESP", "Italia": "ITA", "Grecia": "GRC",
    "Canadá": "CAN", "República Checa": "CZE", "Irlanda": "IRL",
    "Polonia": "POL", "Brasil": "BRA", "México": "MEX", "Chile": "CHL",
    "Colombia": "COL", "Perú": "PER", "Uruguay": "URY",
    "Turquía": "TUR", "Portugal": "PRT", "Países Bajos": "NLD",
    "Holanda": "NLD", "Bélgica": "BEL", "Suecia": "SWE", "Noruega": "NOR",
    "Dinamarca": "DNK", "Finlandia": "FIN", "Suiza": "CHE", "Austria": "AUT",
    "Hungría": "HUN", "Rumania": "ROU", "Ucrania": "UKR", "Israel": "ISR",
    "India": "IND", "Corea del Sur": "KOR", "Australia": "AUS",
    "Nueva Zelanda": "NZL", "Sudáfrica": "ZAF", "Egipto": "EGY",
    "Cuba": "CUB", "Venezuela": "VEN", "Bolivia": "BOL", "Paraguay": "PRY",
    "Ecuador": "ECU", "Nigeria": "NGA", "Marruecos": "MAR", "Croacia": "HRV",
    "Serbia": "SRB", "Bulgaria": "BGR", "Islandia": "ISL", "Albania": "ALB",
}

# Traducción de nombres de país español → inglés
COUNTRY_NAMES_EN = {
    "Estados Unidos": "United States", "Reino Unido": "United Kingdom",
    "Francia": "France", "Japón": "Japan", "Alemania": "Germany",
    "Rusia": "Russia", "China": "China", "Argentina": "Argentina",
    "España": "Spain", "Italia": "Italy", "Grecia": "Greece",
    "Canadá": "Canada", "República Checa": "Czech Republic",
    "Irlanda": "Ireland", "Polonia": "Poland", "Brasil": "Brazil",
    "México": "Mexico", "Chile": "Chile", "Colombia": "Colombia",
    "Perú": "Peru", "Uruguay": "Uruguay", "Turquía": "Turkey",
    "Portugal": "Portugal", "Países Bajos": "Netherlands",
    "Holanda": "Netherlands", "Bélgica": "Belgium", "Suecia": "Sweden",
    "Noruega": "Norway", "Dinamarca": "Denmark", "Finlandia": "Finland",
    "Suiza": "Switzerland", "Austria": "Austria", "Hungría": "Hungary",
    "Rumania": "Romania", "Ucrania": "Ukraine", "Israel": "Israel",
    "India": "India", "Corea del Sur": "South Korea", "Australia": "Australia",
    "Nueva Zelanda": "New Zealand", "Sudáfrica": "South Africa",
    "Egipto": "Egypt", "Cuba": "Cuba", "Venezuela": "Venezuela",
    "Bolivia": "Bolivia", "Paraguay": "Paraguay", "Ecuador": "Ecuador",
    "Nigeria": "Nigeria", "Marruecos": "Morocco", "Croacia": "Croatia",
    "Serbia": "Serbia", "Bulgaria": "Bulgaria", "Islandia": "Iceland",
    "Albania": "Albania",
}

def translate_country(name_es: str) -> str:
    """Devuelve el nombre del país en el idioma activo."""
    if st.session_state.get("lang_selector") == "English":
        return COUNTRY_NAMES_EN.get(name_es, name_es)
    return name_es

# ── Configuración ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Goodreads Explorer",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Lato:wght@300;400;700&family=Merriweather:wght@700&display=swap');

html, body, [class*="css"] {
    font-family: 'Lato', sans-serif;
    background-color: #f9f7f4;
    color: #333333;
}
h1, h2, h3 { font-family: 'Merriweather', serif !important; color: #333333; }

/* Sidebar */
[data-testid="stSidebar"] {
    background-color: #f4f1ec !important;
    border-right: 1px solid #ddd8ce;
}

/* Metric cards — estilo Goodreads: fondo crema, borde sutil */
.metric-card {
    background: #ffffff;
    border: 1px solid #ddd8ce;
    border-radius: 8px;
    padding: 1.2rem 1rem;
    text-align: center;
    color: #333333;
    height: 100%;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06);
}
.metric-card .value {
    font-size: 2rem;
    font-weight: 700;
    color: #382110;
    font-family: 'Merriweather', serif;
    line-height: 1.1;
}
.metric-card .label {
    font-size: 0.72rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: #767676;
    margin-top: 0.3rem;
}

/* Section titles */
.section-title {
    font-family: 'Merriweather', serif;
    font-size: 1.2rem;
    color: #382110;
    border-left: 4px solid #c8a951;
    padding-left: 0.75rem;
    margin: 1.5rem 0 0.8rem;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] { gap: 0; border-bottom: 2px solid #ddd8ce; }
.stTabs [data-baseweb="tab"] {
    font-family: 'Lato', sans-serif;
    font-size: 0.9rem;
    color: #767676;
    padding: 0.6rem 1.2rem;
    border-radius: 0;
}
.stTabs [aria-selected="true"] {
    color: #382110 !important;
    border-bottom: 2px solid #c8a951 !important;
    font-weight: 700;
}

/* Botones y widgets */
.stSlider [data-baseweb="slider"] { color: #c8a951; }
div[data-baseweb="select"] { background-color: #ffffff; }

footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ── Colores (solo usados en la UI, NO en los gráficos) ───────────────────────
GR_BROWN  = "#382110"   # marrón oscuro Goodreads
GR_GOLD   = "#c8a951"   # dorado/beige acento Goodreads
GR_CREAM  = "#f4f1ec"   # fondo crema
GR_BORDER = "#ddd8ce"   # bordes

# Colores de gráficos — sin cambios
RED    = "#e94560"
DARK   = "#1a1a2e"
BLUE   = "#0f3460"
GREEN  = "#53c28b"
ORANGE = "#f5a623"

LAYOUT_BASE = dict(
    font=dict(family="Lato, sans-serif", color="#333333"),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="#fafafa",
    margin=dict(t=40, b=40, l=40, r=20),
    hoverlabel=dict(bgcolor=GR_BROWN, font_color="white", font_size=13),
)

GENRE_COLORS = {
    "sci-fi": "#3a86ff", "fantasy": "#8338ec", "horror": "#e94560",
    "nonfiction": "#06d6a0", "biography": "#fb8500", "post-apocalyptic": "#ffb703",
    "hugo-award": "#ef476f", "favorites": "#ffd166", "political-theory": "#118ab2",
    "geopolitics": "#073b4c", "fulbo": "#2d6a4f", "vampire": "#9d0208",
}

# ── Aliases de autores — agregar acá cualquier nombre duplicado ───────────────
AUTHOR_ALIASES = {
    "Julio Verne": "Jules Verne",
    "Juan Rousseau": "Jean-Jacques Rousseau",
    "Richard Bachman": "Stephen King",  # seudónimo de Stephen King
}

# ── Carga y limpieza ──────────────────────────────────────────────────────────
@st.cache_data
def load_data(file):
    df = pd.read_csv(file)

    # Normalizar nombres
    df.columns = [c.strip() for c in df.columns]
    col_map = {
        "Title": "title", "Author": "author", "My Rating": "my_rating",
        "Number of Pages": "pages", "Year Published": "year_published",
        "Original Publication Year": "year_original", "Date Read": "date_read",
        "Date Added": "date_added", "Bookshelves": "shelves",
        "Exclusive Shelf": "shelf", "Publisher": "publisher",
        "Average Rating": "avg_rating", "My Review": "review",
        "ISBN": "isbn", "ISBN13": "isbn13",
    }
    df = df.rename(columns={k: v for k, v in col_map.items() if k in df.columns})

    # Normalizar espacios y aliases de autores
    if "author" in df.columns:
        df["author"] = df["author"].astype(str).str.strip().str.replace(r"\s+", " ", regex=True)
        df["author"] = df["author"].replace(AUTHOR_ALIASES)

    # Fechas
    df["date_read"]  = pd.to_datetime(df.get("date_read"),  errors="coerce")
    df["date_added"] = pd.to_datetime(df.get("date_added"), errors="coerce")

    # Año de publicación (original preferido)
    df["pub_year"] = pd.to_numeric(
        df.get("year_original", df.get("year_published", None)), errors="coerce"
    ).combine_first(
        pd.to_numeric(df.get("year_published", None), errors="coerce")
    )

    # Año / mes de lectura
    df["read_year"]  = df["date_read"].dt.year
    df["read_month"] = df["date_read"].dt.month
    df["pages"]      = pd.to_numeric(df.get("pages", None), errors="coerce")

    # Géneros: explotar shelves en lista
    def parse_shelves(s):
        if pd.isna(s) or s.strip() == "":
            return []
        return [g.strip() for g in s.split(",")]

    df["genre_list"] = df["shelves"].apply(parse_shelves)
    df["primary_genre"] = df["genre_list"].apply(
        lambda lst: lst[0] if lst else "sin categoría"
    )

    # Filtrar solo leídos
    if "shelf" in df.columns:
        df_read = df[df["shelf"] == "read"].copy()
    else:
        df_read = df.copy()

    return df_read

def metric_card(col, value, label):
    col.markdown(f"""
    <div class="metric-card">
      <div class="value">{value}</div>
      <div class="label">{label}</div>
    </div>
    """, unsafe_allow_html=True)

def goodreads_url(row):
    """Genera URL de búsqueda en Goodreads usando ISBN13, ISBN o título."""
    for col in ["isbn13", "isbn"]:
        val = str(row.get(col, "")).strip().strip("=").strip('"')
        if val and val not in ["nan", "", "0"]:
            return f"https://www.goodreads.com/search?q={val}"
    # Fallback por título + autor
    title  = str(row.get("title", "")).replace(" ", "+")
    author = str(row.get("author", "")).replace(" ", "+")
    return f"https://www.goodreads.com/search?q={title}+{author}"

def add_goodreads_links(df_display):
    """Agrega columna de links HTML a un dataframe para mostrar en st.markdown."""
    return df_display

def show_books_table(df_src, sort_col="date_read", height=320):
    """Muestra tabla de libros con link a Goodreads."""
    cols_show = [c for c in ["title","author","pub_year","date_read","my_rating","pages"] if c in df_src.columns]
    tbl = df_src[cols_show].copy()
    tbl["🔗"] = df_src.apply(lambda r: f'<a href="{goodreads_url(r)}" target="_blank">Goodreads</a>', axis=1)
    tbl = tbl.rename(columns={
        "title":     t("col_title"),
        "author":    t("col_author"),
        "pub_year":  t("col_pub_year"),
        "date_read": t("col_date_read"),
        "my_rating": t("col_rating"),
        "pages":     t("col_pages"),
    })
    date_col = t("col_date_read")
    pub_col  = t("col_pub_year")
    if date_col in tbl.columns:
        tbl = tbl.sort_values(date_col, ascending=False)
        tbl[date_col] = tbl[date_col].dt.strftime(t("date_format"))
    if pub_col in tbl.columns:
        tbl[pub_col] = tbl[pub_col].fillna(0).astype(int)
    st.write(tbl.to_html(escape=False, index=False), unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════
# IDIOMA — selector antes de todo
# ════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    lang_label = st.selectbox(
        "🌐 Idioma / Language",
        options=list(LANGUAGES.keys()),
        index=0,
        key="lang_selector",
    )
    lang_code = LANGUAGES[lang_label]
    st.session_state["locale"] = load_locale(lang_code)

# ════════════════════════════════════════════════════════════════════════════
# HEADER
# ════════════════════════════════════════════════════════════════════════════
st.markdown(f"# 📚 {t('app_title')}")
st.markdown(f"*{t('app_subtitle')}*")
st.divider()

# ── Sidebar: carga + filtros ──────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"### 📂 {t('sidebar_load')}")
    uploaded = st.file_uploader(
        t("sidebar_upload_label"),
        type=["csv"],
        help=t("sidebar_upload_help"),
    )
    st.markdown("---")
    st.markdown(f"**{t('sidebar_how_to')}**\n\n{t('sidebar_how_to_steps')}")

if not uploaded:
    st.info(t("no_file"))
    st.stop()

df = load_data(uploaded)

if df.empty:
    st.warning(t("no_read_books"))
    st.stop()

# Sidebar filtros (después de cargar datos)
with st.sidebar:
    st.markdown(f"### 🔎 {t('sidebar_filters')}")

    # Año de lectura
    if df["read_year"].notna().any():
        yr_min, yr_max = int(df["read_year"].min()), int(df["read_year"].max())
        yr_range = st.slider(t("sidebar_read_year"), yr_min, yr_max, (yr_min, yr_max))
    else:
        yr_range = None

    # Año de publicación
    if df["pub_year"].notna().any():
        pub_min = int(df["pub_year"].dropna().min())
        pub_max = int(df["pub_year"].dropna().max())
        pub_range = st.slider(t("sidebar_pub_year"), pub_min, pub_max, (pub_min, pub_max))
    else:
        pub_range = None

    # Géneros
    all_genres = sorted(set(g for lst in df["genre_list"] for g in lst if g))
    all_genres_with_none = all_genres + ["sin categoría"]
    genres_sel = st.multiselect(t("sidebar_genres"), all_genres_with_none, default=all_genres_with_none)

    # Rating
    ratings_all = sorted(df["my_rating"].dropna().unique().tolist())
    ratings_sel = st.multiselect(
        t("sidebar_rating"),
        options=ratings_all,
        default=ratings_all,
        format_func=lambda x: f"{'⭐'*int(x)} ({int(x)})" if x > 0 else t("no_rating"),
    )

    st.markdown("---")
    st.markdown(f"### {t('sidebar_format_filters')}")
    exclude_manga = st.checkbox(t("exclude_manga"))
    exclude_light_novel = st.checkbox(t("exclude_light_novel"))
    exclude_comics = st.checkbox(t("exclude_comics"))

# Aplicar filtros
mask = pd.Series([True] * len(df), index=df.index)
if yr_range:
    mask &= df["read_year"].between(*yr_range) | df["read_year"].isna()
if pub_range:
    mask &= df["pub_year"].fillna(9999).between(*pub_range)
if genres_sel and len(genres_sel) < len(all_genres_with_none):
    include_none = "sin categoría" in genres_sel
    mask &= df["genre_list"].apply(
        lambda lst: (any(g in genres_sel for g in lst)) or (include_none and lst == [])
    )
if ratings_sel is not None:
    mask &= df["my_rating"].isin(ratings_sel)
if exclude_manga:
    mask &= df["genre_list"].apply(lambda lst: "manga" not in lst)
if exclude_light_novel:
    mask &= df["genre_list"].apply(lambda lst: "light-novel" not in lst)
if exclude_comics:
    mask &= df["genre_list"].apply(lambda lst: "comic" not in lst)

dff = df[mask].copy()

# ════════════════════════════════════════════════════════════════════════════
# MÉTRICAS GLOBALES
# ════════════════════════════════════════════════════════════════════════════
st.markdown(f'<div class="section-title">{t("summary_title")}</div>', unsafe_allow_html=True)
c1, c2, c3, c4, c5, c6 = st.columns(6)
metric_card(c1, f"{len(dff):,}", t("metric_books"))

total_pages = int(dff["pages"].sum(skipna=True))
metric_card(c2, f"{total_pages:,}", t("metric_pages"))

metric_card(c3, dff["author"].nunique(), t("metric_authors"))

rated = dff[dff["my_rating"] > 0]["my_rating"]
avg_r = rated.mean() if len(rated) else 0
metric_card(c4, f"{avg_r:.1f} ⭐", t("metric_rating"))

top_author = dff["author"].value_counts().idxmax() if len(dff) else "—"
top_count  = dff["author"].value_counts().max() if len(dff) else 0
metric_card(c5, str(top_count), f"{t('metric_top_author')}: {top_author.split(',')[0]}")

fav5 = len(dff[dff["my_rating"] == 5])
metric_card(c6, fav5, t("metric_five_stars"))

st.divider()

# ════════════════════════════════════════════════════════════════════════════
# TABS
# ════════════════════════════════════════════════════════════════════════════
tab1, tab2, tab3, tab4 = st.tabs([
    t("tab_scatter"),
    t("tab_authors"),
    t("tab_history"),
    t("tab_genres"),
])


# ─────────────────────────────────────────────────────────────────────────────
# TAB 1: SCATTER interactivo
# ─────────────────────────────────────────────────────────────────────────────
with tab1:
    st.markdown(t("scatter_hint"))

    scatter_df = dff.dropna(subset=["pub_year", "date_read"]).copy()
    scatter_df["read_float"] = (
        scatter_df["date_read"].dt.year
        + scatter_df["date_read"].dt.dayofyear / 365.25
    )

    # Rangos fijos de los ejes
    x_min = float(scatter_df["read_float"].min()) - 0.5
    x_max = float(datetime.now().year) + 0.5
    y_min = float(scatter_df["pub_year"].min()) - 2
    y_max = float(scatter_df["pub_year"].max()) + 2

    # Construir hover text
    def hover_text(row):
        rating_str = "⭐" * int(row.get("my_rating", 0)) if row.get("my_rating", 0) > 0 else t("card_no_rating")
        pages_str  = f"{int(row['pages'])} {t('col_pages').lower()}" if pd.notna(row.get("pages")) else ""
        genre_str  = ", ".join(row.get("genre_list", []))
        url        = goodreads_url(row)
        parts = [
            f"<b>{row['title']}</b>",
            f"{row['author']}",
            f"{t('card_published')}: {int(row['pub_year'])}",
            f"{t('card_read')}: {row['date_read'].strftime(t('date_format'))}",
            f"{rating_str}",
        ]
        if pages_str:  parts.append(pages_str)
        if genre_str:  parts.append(genre_str)
        parts.append(f"<a href='{url}' target='_blank'>{t('card_link')}</a>")
        return "<br>".join(parts)

    scatter_df["hover"] = scatter_df.apply(hover_text, axis=1)

    # Construir un trace por cada género considerando TODOS los géneros del libro
    fig = go.Figure()

    all_scatter_genres = sorted(set(g for lst in scatter_df["genre_list"] for g in lst if g))
    if not all_scatter_genres:
        all_scatter_genres = ["sin categoría"]

    for genre in all_scatter_genres:
        gdf = scatter_df[scatter_df["genre_list"].apply(lambda lst: genre in lst)]
        if gdf.empty:
            continue
        fig.add_trace(go.Scatter(
            x=gdf["read_float"],
            y=gdf["pub_year"],
            mode="markers",
            name=genre,
            marker=dict(
                size=10,
                color=GENRE_COLORS.get(genre, "#888888"),
                opacity=0.82,
                line=dict(width=0.8, color="white"),
            ),
            text=gdf["hover"],
            hovertemplate="%{text}<extra></extra>",
        ))

    fig.update_layout(
        **LAYOUT_BASE,
        height=620,
        width=620,
        xaxis=dict(
            title=t("scatter_x"),
            tickformat="d",
            gridcolor="#ebebeb",
            zeroline=False,
            range=[x_min, x_max],
        ),
        yaxis=dict(
            title=t("scatter_y"),
            gridcolor="#ebebeb",
            zeroline=False,
            range=[y_min, y_max],
        ),
        legend=dict(
            title=t("scatter_legend"),
            orientation="v",
            bgcolor="rgba(255,255,255,0.9)",
            bordercolor="#ddd",
            borderwidth=1,
        ),
        dragmode="zoom",
        title=t("scatter_title"),
    )

    sel_scatter = st.plotly_chart(fig, use_container_width=True,
                                  on_select="rerun", key="chart_scatter")

    # ── Ficha fija al hacer clic en un punto ────────────────────────────────
    try:
        pts = sel_scatter.selection.get("points", [])
        if pts:
            pt = pts[0]
            read_val = pt.get("x")
            pub_val  = pt.get("y")
            match = scatter_df[
                (scatter_df["read_float"].round(3) == round(read_val, 3)) &
                (scatter_df["pub_year"] == pub_val)
            ]
            if match.empty:
                scatter_df["_dist"] = (
                    (scatter_df["read_float"] - read_val).abs() +
                    (scatter_df["pub_year"]   - pub_val).abs()
                )
                match = scatter_df.nsmallest(1, "_dist")

            if not match.empty:
                row = match.iloc[0]
                rating_str = "⭐" * int(row.get("my_rating", 0)) if row.get("my_rating", 0) > 0 else t("card_no_rating")
                pages_str  = f"{int(row['pages'])} {t('col_pages').lower()}" if pd.notna(row.get("pages")) else "—"
                genres_str = ", ".join(row.get("genre_list", [])) or "—"
                url        = goodreads_url(row)

                st.markdown(f"""
                <div style="
                    background: #ffffff;
                    border: 1px solid #ddd8ce;
                    border-radius: 8px;
                    padding: 1.2rem 1.5rem;
                    color: #333333;
                    max-width: 600px;
                    margin: 0.5rem 0 1rem;
                    box-shadow: 0 1px 3px rgba(0,0,0,0.08);
                ">
                    <div style="font-size:1.2rem; font-weight:700; color:#382110; margin-bottom:0.4rem; font-family:'Merriweather',serif;">
                        {row['title']}
                    </div>
                    <div style="font-size:0.95rem; color:#767676; margin-bottom:0.8rem;">
                        {row['author']}
                    </div>
                    <div style="display:grid; grid-template-columns:1fr 1fr; gap:0.4rem 2rem; font-size:0.88rem; color:#333333;">
                        <span>📅 {t('card_published')}: <b>{int(row['pub_year'])}</b></span>
                        <span>📖 {t('card_read')}: <b>{row['date_read'].strftime(t('date_format'))}</b></span>
                        <span>⭐ {t('card_rating')}: <b>{rating_str}</b></span>
                        <span>📄 {t('card_pages')}: <b>{pages_str}</b></span>
                        <span style="grid-column:1/-1">🏷️ {t('card_genres')}: <b>{genres_str}</b></span>
                    </div>
                    <div style="margin-top:0.9rem;">
                        <a href="{url}" target="_blank" style="
                            background:#382110; color:#f4f1ec; padding:0.4rem 1rem;
                            border-radius:4px; text-decoration:none; font-size:0.85rem;
                        ">{t('card_link')}</a>
                    </div>
                </div>
                """, unsafe_allow_html=True)
    except Exception:
        pass

    with st.expander(t("scatter_table_expander")):
        cols_show = [c for c in ["title","author","pub_year","date_read","my_rating","pages","primary_genre"] if c in dff.columns]
        show_df = dff[cols_show].copy()
        show_df["goodreads"] = dff.apply(lambda r: f'<a href="{goodreads_url(r)}" target="_blank">🔗</a>', axis=1)
        show_df = show_df.rename(columns={
            "title": t("col_title"), "author": t("col_author"), "pub_year": t("col_pub_year"),
            "date_read": t("col_date_read"), "my_rating": t("col_rating"), "pages": t("col_pages"),
            "primary_genre": t("col_genre"), "goodreads": t("col_goodreads"),
        }).sort_values(t("col_date_read"), ascending=False)
        date_col = t("col_date_read")
        if date_col in show_df.columns:
            show_df[date_col] = show_df[date_col].dt.strftime(t("date_format"))
        pub_col = t("col_pub_year")
        if pub_col in show_df.columns:
            show_df[pub_col] = show_df[pub_col].fillna(0).astype(int)
        st.write(show_df.to_html(escape=False, index=False), unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# TAB 2: AUTORES
# ─────────────────────────────────────────────────────────────────────────────
with tab2:
    st.caption(t("authors_hint"))
    top_n = st.slider(t("authors_top_n"), 5, 30, 15, key="top_n")

    col_a, col_b, col_c2 = st.columns(3)

    # ── Preparar los tres datasets ───────────────────────────────────────────
    bks_label  = t("col_books")
    pgs_label  = t("col_pages")
    rat_label  = t("col_rating")
    auth_label = t("col_author")

    auth_cnt = (
        dff["author"].value_counts().head(top_n)
        .reset_index().rename(columns={"count": bks_label, "author": auth_label})
    )

    auth_pag = (
        dff[dff["pages"].notna()]
        .groupby("author")["pages"].sum()
        .sort_values(ascending=False).head(top_n)
        .reset_index().rename(columns={"author": auth_label, "pages": pgs_label})
    )
    auth_pag[pgs_label] = auth_pag[pgs_label].astype(int)

    auth_rat = (
        dff[dff["my_rating"] > 0]
        .groupby("author")
        .agg(**{bks_label: ("title","count"), rat_label: ("my_rating","mean")})
        .query(f"`{bks_label}` >= 2")
        .sort_values(rat_label, ascending=False)
        .head(top_n).reset_index()
        .rename(columns={"author": auth_label})
    )
    auth_rat[rat_label] = auth_rat[rat_label].round(2)

    chart_h = max(380, top_n * 28)

    with col_a:
        st.markdown(f'<div class="section-title">{t("authors_by_books")}</div>', unsafe_allow_html=True)
        fig_a = px.bar(auth_cnt, x=bks_label, y=auth_label, orientation="h")
        fig_a.update_traces(marker_color=BLUE)
        fig_a.update_layout(**LAYOUT_BASE, height=chart_h,
                            yaxis=dict(autorange="reversed"))
        sel_a = st.plotly_chart(fig_a, use_container_width=True,
                                on_select="rerun", key="chart_authors_count")

    with col_b:
        st.markdown(f'<div class="section-title">{t("authors_by_pages")}</div>', unsafe_allow_html=True)
        fig_b2 = px.bar(auth_pag, x=pgs_label, y=auth_label, orientation="h")
        fig_b2.update_traces(marker_color=BLUE)
        fig_b2.update_layout(**LAYOUT_BASE, height=chart_h,
                             yaxis=dict(autorange="reversed"))
        sel_b2 = st.plotly_chart(fig_b2, use_container_width=True,
                                 on_select="rerun", key="chart_authors_pages")

    with col_c2:
        st.markdown(f'<div class="section-title">{t("authors_by_rating")}</div>', unsafe_allow_html=True)
        fig_b = px.bar(auth_rat, x=rat_label, y=auth_label, orientation="h",
                       color=rat_label, color_continuous_scale=["#e94560", "#f5a623", "#53c28b"],
                       range_x=[0, 5.3], hover_data={bks_label: True})
        fig_b.update_layout(**LAYOUT_BASE, height=chart_h,
                            yaxis=dict(autorange="reversed"), coloraxis_showscale=False)
        sel_b = st.plotly_chart(fig_b, use_container_width=True,
                                on_select="rerun", key="chart_authors_rating")

    # ── Tabla al hacer clic ──────────────────────────────────────────────────
    selected_author = None

    for sel, df_ref in [
        (sel_a,  auth_cnt),
        (sel_b2, auth_pag),
        (sel_b,  auth_rat),
    ]:
        try:
            pts = sel.selection.get("points", [])
            if pts:
                idx = pts[0].get("point_index", None)
                if idx is not None:
                    selected_author = df_ref.iloc[idx][auth_label]
                    break
        except Exception:
            pass

    if selected_author:
        st.markdown(f'<div class="section-title">{t("authors_selected_title")} {selected_author}</div>', unsafe_allow_html=True)
        author_books = dff[dff["author"] == selected_author].copy()
        show_books_table(author_books)
    else:
        st.markdown(f'<div class="section-title">{t("authors_detail_title")}</div>', unsafe_allow_html=True)
        agg = {"title": "count"}
        if "pages"     in dff.columns: agg["pages"]     = "sum"
        if "my_rating" in dff.columns: agg["my_rating"] = "mean"
        auth_table = (
            dff.groupby("author").agg(agg)
            .rename(columns={"title": bks_label, "pages": pgs_label, "my_rating": t("col_rating_avg")})
            .sort_values(bks_label, ascending=False).reset_index()
            .rename(columns={"author": auth_label})
        )
        rat_avg_col = t("col_rating_avg")
        if rat_avg_col in auth_table.columns:
            auth_table[rat_avg_col] = auth_table[rat_avg_col].round(2)
        if pgs_label in auth_table.columns:
            auth_table[pgs_label] = auth_table[pgs_label].fillna(0).astype(int)
        st.dataframe(auth_table, use_container_width=True, height=320)

    # ── Mapa mundial de autores ─────────────────────────────────────────────
    author_countries = load_author_countries()

    st.divider()
    st.markdown(f'<div class="section-title">{t("authors_map_title")}</div>', unsafe_allow_html=True)

    if not author_countries:
        st.warning(
            f"No se encontró o no se pudo leer `locales/author_countries.json`. "
            f"Verificá que el archivo esté en la misma carpeta que `goodreads_explorer.py`, "
            f"dentro de una subcarpeta llamada `locales`."
        )
    else:
        st.caption(t("authors_map_hint"))

        # Asignar país a cada libro vía el cache de autores
        dff_geo = dff.copy()
        dff_geo["author_country"] = dff_geo["author"].map(author_countries)
        dff_geo = dff_geo.dropna(subset=["author_country"])

        if dff_geo.empty:
            st.info(t("authors_map_no_data"))
        else:
            country_label = t("authors_map_country_col")

            # Traducir nombres de país al idioma activo
            dff_geo["author_country_display"] = dff_geo["author_country"].apply(translate_country)

            iso3_map = {translate_country(k): v for k, v in COUNTRY_ISO3.items()}

            def build_country_df(agg_col, agg_func, label):
                """Construye el dataframe de países con ISO3 para el mapa."""
                if agg_func == "nunique":
                    cnt = (
                        dff_geo.groupby("author_country_display")[agg_col].nunique()
                        .reset_index().rename(columns={"author_country_display": country_label, agg_col: label})
                    )
                else:
                    cnt = (
                        dff_geo.groupby("author_country_display")[agg_col].sum()
                        .reset_index().rename(columns={"author_country_display": country_label, agg_col: label})
                    )
                cnt["iso3"] = cnt[country_label].map(iso3_map)
                return cnt

            country_authors_df = build_country_df("author", "nunique", auth_label)
            country_pages_df   = build_country_df("pages",  "sum",     pgs_label)

            # Libros: contar filas por país directamente
            country_books_df = (
                dff_geo.groupby("author_country_display").size()
                .reset_index(name=bks_label)
                .rename(columns={"author_country_display": country_label})
            )
            country_books_df["iso3"] = country_books_df[country_label].map(iso3_map)

            # Avisar países sin ISO3 (usando el df de autores como referencia)
            missing_iso = country_authors_df[country_authors_df["iso3"].isna()][country_label].tolist()
            if missing_iso:
                st.caption(
                    f"⚠️ País(es) sin código ISO asignado (no aparecen en el mapa): {', '.join(missing_iso)}. "
                    f"Agregalos a COUNTRY_ISO3 en el código."
                )

            country_authors_df = country_authors_df.dropna(subset=["iso3"])
            country_books_df   = country_books_df.dropna(subset=["iso3"])
            country_pages_df   = country_pages_df.dropna(subset=["iso3"])

            def make_choropleth(df, color_col, key):
                fig = px.choropleth(
                    df, locations="iso3", color=color_col, hover_name=country_label,
                    color_continuous_scale=["#dbe9f4", BLUE, "#382110"],
                )
                fig.update_layout(
                    **LAYOUT_BASE, height=480,
                    geo=dict(
                        bgcolor="rgba(0,0,0,0)", showframe=False,
                        landcolor="#ededed", coastlinecolor="#cccccc",
                        showcountries=True, countrycolor="#b5b0a6", countrywidth=0.6,
                    ),
                )
                return st.plotly_chart(fig, use_container_width=True,
                                       on_select="rerun", key=key)

            map_tab1, map_tab2, map_tab3 = st.tabs([
                f"👤 {t('metric_authors')}",
                f"📚 {t('metric_books')}",
                f"📄 {t('metric_pages')}",
            ])

            with map_tab1:
                sel_map = make_choropleth(country_authors_df, auth_label, "chart_author_map")
                active_df = country_authors_df

            with map_tab2:
                sel_map = make_choropleth(country_books_df, bks_label, "chart_books_map")
                active_df = country_books_df

            with map_tab3:
                sel_map = make_choropleth(country_pages_df, pgs_label, "chart_pages_map")
                active_df = country_pages_df

            # Clic en un país -> mostrar autores y libros de ese país
            try:
                pts = sel_map.selection.get("points", [])
                if pts:
                    idx = pts[0].get("point_index", None)
                    if idx is not None:
                        country_display = active_df.iloc[idx][country_label]
                        country_authors = sorted(
                            dff_geo[dff_geo["author_country_display"] == country_display]["author"].unique()
                        )
                        st.markdown(
                            f'<div class="section-title">📍 {country_display} — {", ".join(country_authors)}</div>',
                            unsafe_allow_html=True,
                        )
                        show_books_table(dff_geo[dff_geo["author_country_display"] == country_display])
            except Exception:
                pass

            unmatched = sorted(set(dff["author"].unique()) - set(author_countries.keys()))
            if unmatched:
                with st.expander(t("authors_map_unmatched")):
                    st.write(", ".join(unmatched))


# ─────────────────────────────────────────────────────────────────────────────
# TAB 3: HISTORIAL & PÁGINAS
# ─────────────────────────────────────────────────────────────────────────────
with tab3:
    st.caption(t("history_hint"))
    col_c, col_d = st.columns(2)

    MESES = t("months")

    with col_c:
        st.markdown(f'<div class="section-title">{t("history_books_year")}</div>', unsafe_allow_html=True)
        by_yr = dff.groupby("read_year").size().reset_index(name=bks_label).dropna()
        by_yr["read_year"] = by_yr["read_year"].astype(int)
        fig_yr = px.bar(by_yr, x="read_year", y=bks_label,
                        labels={"read_year": t("col_year")})
        fig_yr.update_traces(marker_color=BLUE)
        fig_yr.update_layout(**LAYOUT_BASE, height=300)
        sel_yr = st.plotly_chart(fig_yr, use_container_width=True,
                                 on_select="rerun", key="chart_by_year")

    with col_d:
        st.markdown(f'<div class="section-title">{t("history_books_month")}</div>', unsafe_allow_html=True)
        by_mo = dff.groupby("read_month").size().reset_index(name=bks_label).dropna()
        by_mo[t("col_month")] = by_mo["read_month"].apply(lambda x: MESES[int(x)-1])
        fig_mo = px.bar(by_mo, x=t("col_month"), y=bks_label,
                        category_orders={t("col_month"): MESES})
        fig_mo.update_traces(marker_color=BLUE)
        fig_mo.update_layout(**LAYOUT_BASE, height=300)
        sel_mo = st.plotly_chart(fig_mo, use_container_width=True,
                                 on_select="rerun", key="chart_by_month")

    # ── Tabla al hacer clic en año o mes ────────────────────────────────────
    selected_label = None
    filtered_books = None

    try:
        pts = sel_yr.selection.get("points", [])
        if pts:
            idx = pts[0].get("point_index", None)
            if idx is not None:
                yr_val = int(by_yr.iloc[idx]["read_year"])
                selected_label = f"{t('history_selected_year')} {yr_val}"
                filtered_books = dff[dff["read_year"] == yr_val]
    except Exception:
        pass

    if filtered_books is None:
        try:
            pts = sel_mo.selection.get("points", [])
            if pts:
                idx = pts[0].get("point_index", None)
                if idx is not None:
                    mo_val = int(by_mo.iloc[idx]["read_month"])
                    selected_label = f"{t('history_selected_month')} {MESES[mo_val-1]}"
                    filtered_books = dff[dff["read_month"] == mo_val]
        except Exception:
            pass

    if filtered_books is not None and selected_label:
        st.markdown(f'<div class="section-title">{selected_label}</div>', unsafe_allow_html=True)
        show_books_table(filtered_books)

    # Curva acumulada — libros
    st.markdown(f'<div class="section-title">{t("history_cumulative")}</div>', unsafe_allow_html=True)
    cum = (
        dff.dropna(subset=["date_read"])
        .sort_values("date_read")
        .reset_index(drop=True)
    )
    cum[t("metric_books")] = range(1, len(cum)+1)
    fig_cum = px.line(cum, x="date_read", y=t("metric_books"),
                      labels={"date_read": t("col_date_read")},
                      hover_data={"title": True} if "title" in cum.columns else {})
    fig_cum.update_traces(line_color=RED, line_width=2.5)
    fig_cum.update_layout(**LAYOUT_BASE, height=300)
    st.plotly_chart(fig_cum, use_container_width=True)

    # Curva acumulada — páginas
    if "pages" in cum.columns:
        st.markdown(f'<div class="section-title">{t("history_cumulative_pages")}</div>', unsafe_allow_html=True)
        cum_pg = cum.copy()
        cum_pg[pgs_label] = cum_pg["pages"].fillna(0).cumsum().astype(int)
        fig_cum_pg = px.line(cum_pg, x="date_read", y=pgs_label,
                             labels={"date_read": t("col_date_read")},
                             hover_data={"title": True} if "title" in cum_pg.columns else {})
        fig_cum_pg.update_traces(line_color=GREEN, line_width=2.5)
        fig_cum_pg.update_layout(**LAYOUT_BASE, height=300)
        st.plotly_chart(fig_cum_pg, use_container_width=True)

    # Páginas por año
    if "pages" in dff.columns:
        st.markdown(f'<div class="section-title">{t("history_pages_year")}</div>', unsafe_allow_html=True)
        pg_yr = dff.groupby("read_year")["pages"].sum().reset_index(name=pgs_label).dropna()
        pg_yr["read_year"] = pg_yr["read_year"].astype(int)
        fig_pg = px.area(pg_yr, x="read_year", y=pgs_label,
                         labels={"read_year": t("col_year")},
                         color_discrete_sequence=[RED])
        fig_pg.update_layout(**LAYOUT_BASE, height=280)
        st.plotly_chart(fig_pg, use_container_width=True)

    # ── Desglose mensual ─────────────────────────────────────────────────────
    st.divider()
    st.markdown(f'<div class="section-title">{t("history_monthly_title")}</div>', unsafe_allow_html=True)
    st.caption(t("history_monthly_hint"))

    if dff["date_read"].notna().any():
        monthly = dff.dropna(subset=["date_read"]).copy()
        monthly["anio_mes"] = monthly["date_read"].dt.to_period("M").astype(str)
        monthly["anio_mes_dt"] = pd.to_datetime(monthly["anio_mes"])

        col_m1, col_m2 = st.columns(2)

        with col_m1:
            st.markdown(f"**{t('history_books_by_month')}**")
            libros_mes = (
                monthly.groupby("anio_mes_dt").size()
                .reset_index(name=bks_label)
                .sort_values("anio_mes_dt")
            )
            fig_lm = px.bar(libros_mes, x="anio_mes_dt", y=bks_label,
                            color=bks_label, color_continuous_scale=[BLUE, RED],
                            labels={"anio_mes_dt": t("col_month")})
            fig_lm.update_layout(**LAYOUT_BASE, height=320,
                                 coloraxis_showscale=False,
                                 xaxis=dict(tickformat="%b %Y", tickangle=-45))
            sel_lm = st.plotly_chart(fig_lm, use_container_width=True,
                                     on_select="rerun", key="chart_libros_mes")

        with col_m2:
            if "pages" in monthly.columns:
                st.markdown(f"**{t('history_pages_by_month')}**")
                pags_mes = (
                    monthly.groupby("anio_mes_dt")["pages"].sum()
                    .reset_index(name=pgs_label)
                    .sort_values("anio_mes_dt")
                )
                fig_pm = px.bar(pags_mes, x="anio_mes_dt", y=pgs_label,
                                color=pgs_label, color_continuous_scale=[BLUE, GREEN],
                                labels={"anio_mes_dt": t("col_month")})
                fig_pm.update_layout(**LAYOUT_BASE, height=320,
                                     coloraxis_showscale=False,
                                     xaxis=dict(tickformat="%b %Y", tickangle=-45))
                sel_pm = st.plotly_chart(fig_pm, use_container_width=True,
                                         on_select="rerun", key="chart_pags_mes")
            else:
                sel_pm = None

        filtered_monthly = None
        label_monthly = None

        for sel_m, df_ref_m in [(sel_lm, libros_mes), (sel_pm, pags_mes) if "pages" in monthly.columns else (None, None)]:
            if sel_m is None:
                continue
            try:
                pts = sel_m.selection.get("points", [])
                if pts:
                    idx = pts[0].get("point_index", None)
                    if idx is not None:
                        mes_dt = df_ref_m.iloc[idx]["anio_mes_dt"]
                        label_monthly = f"{t('history_selected_month_label')} {mes_dt.strftime(t('date_format'))}"
                        filtered_monthly = monthly[monthly["anio_mes_dt"] == mes_dt]
                        break
            except Exception:
                pass

        if filtered_monthly is not None and label_monthly:
            st.markdown(f'<div class="section-title">{label_monthly}</div>', unsafe_allow_html=True)
            show_books_table(filtered_monthly)


# ─────────────────────────────────────────────────────────────────────────────
# TAB 4: GÉNEROS & RANKINGS
# ─────────────────────────────────────────────────────────────────────────────
with tab4:
    st.caption(t("genres_hint"))
    col_e, col_f = st.columns(2)

    dec_label    = t("col_decade")
    genre_label  = t("col_genre")
    stars_label  = t("col_stars")
    qty_label    = t("col_quantity")

    # Preparar datos de década
    dec = dff.dropna(subset=["pub_year"]).copy()
    dec[dec_label] = (dec["pub_year"] // 10 * 10).astype(int).astype(str) + "s"
    dec_cnt = dec.groupby(dec_label).size().reset_index(name=bks_label).sort_values(dec_label)

    # Preparar datos de género
    exploded = dff.explode("genre_list").rename(columns={"genre_list": genre_label})
    exploded = exploded[exploded[genre_label].notna() & (exploded[genre_label] != "")]
    genre_cnt = exploded[genre_label].value_counts().reset_index()
    genre_cnt.columns = [genre_label, bks_label]

    with col_e:
        st.markdown(f'<div class="section-title">{t("genres_by_genre")}</div>', unsafe_allow_html=True)
        bar_colors = [GENRE_COLORS.get(g, "#888888") for g in genre_cnt[genre_label]]
        fig_g = px.bar(
            genre_cnt, x=bks_label, y=genre_label, orientation="h",
        )
        fig_g.update_traces(marker_color=bar_colors)
        fig_g.update_layout(
            **LAYOUT_BASE, height=max(300, len(genre_cnt)*26),
            yaxis=dict(autorange="reversed"), showlegend=False,
        )
        sel_genre = st.plotly_chart(fig_g, use_container_width=True,
                                    on_select="rerun", key="chart_genres")

    with col_f:
        st.markdown(f'<div class="section-title">{t("genres_by_rating")}</div>', unsafe_allow_html=True)
        rat_df = dff[dff["my_rating"] > 0]["my_rating"].value_counts().sort_index().reset_index()
        rat_df.columns = [rat_label, qty_label]
        rat_df[stars_label] = rat_df[rat_label].apply(lambda x: "⭐"*int(x))
        fig_rat = px.bar(rat_df, x=stars_label, y=qty_label,
                         color=qty_label, color_continuous_scale=[ORANGE, RED])
        fig_rat.update_layout(**LAYOUT_BASE, height=300, coloraxis_showscale=False)
        sel_rat = st.plotly_chart(fig_rat, use_container_width=True,
                                  on_select="rerun", key="chart_ratings")

        st.markdown(f'<div class="section-title">{t("genres_by_decade")}</div>', unsafe_allow_html=True)
        fig_dec = px.bar(dec_cnt, x=dec_label, y=bks_label,
                         color=bks_label, color_continuous_scale=[BLUE, RED])
        fig_dec.update_layout(**LAYOUT_BASE, height=280, coloraxis_showscale=False)
        sel_dec = st.plotly_chart(fig_dec, use_container_width=True,
                                  on_select="rerun", key="chart_decades")

    # ── Tabla al hacer clic ──────────────────────────────────────────────────
    selected_label = None
    filtered_books = None

    try:
        pts = sel_genre.selection.get("points", [])
        if pts:
            idx = pts[0].get("point_index", None)
            if idx is not None:
                genre_val = genre_cnt.iloc[idx][genre_label]
                selected_label = f"{t('genres_selected_genre')} {genre_val}"
                filtered_books = dff[dff["genre_list"].apply(lambda lst: genre_val in lst)]
    except Exception:
        pass

    if filtered_books is None:
        try:
            pts = sel_rat.selection.get("points", [])
            if pts:
                idx = pts[0].get("point_index", None)
                if idx is not None:
                    rat_val = int(rat_df.iloc[idx][rat_label])
                    star_word = t("genres_selected_rating_singular") if rat_val == 1 else t("genres_selected_rating_plural")
                    selected_label = f"⭐ {rat_val} {star_word}"
                    filtered_books = dff[dff["my_rating"] == rat_val]
        except Exception:
            pass

    if filtered_books is None:
        try:
            pts = sel_dec.selection.get("points", [])
            if pts:
                idx = pts[0].get("point_index", None)
                if idx is not None:
                    dec_val = dec_cnt.iloc[idx][dec_label]
                    selected_label = f"{t('genres_selected_decade')} {dec_val}"
                    filtered_books = dec[dec[dec_label] == dec_val]
        except Exception:
            pass

    if filtered_books is not None and selected_label:
        st.markdown(f'<div class="section-title">{selected_label}</div>', unsafe_allow_html=True)
        show_books_table(filtered_books)

    # Rankings especiales
    st.markdown(f'<div class="section-title">{t("rankings_title")}</div>', unsafe_allow_html=True)
    r1, r2, r3 = st.columns(3)

    with r1:
        st.markdown(f"**{t('rankings_longest')}**")
        if "pages" in dff.columns:
            show_books_table(dff.dropna(subset=["pages"]).nlargest(8, "pages"))

    with r2:
        st.markdown(f"**{t('rankings_five_stars')}**")
        show_books_table(dff[dff["my_rating"] == 5])

    with r3:
        st.markdown(f"**{t('rankings_recent')}**")
        show_books_table(dff.dropna(subset=["date_read"]).nlargest(10, "date_read"))
