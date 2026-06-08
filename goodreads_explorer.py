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

# ── Configuración ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Goodreads Explorer",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;900&family=Source+Sans+3:wght@300;400;600&display=swap');
html, body, [class*="css"] { font-family: 'Source Sans 3', sans-serif; }
h1, h2, h3 { font-family: 'Playfair Display', serif !important; }
.metric-card {
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
    border: 1px solid #0f3460;
    border-radius: 12px;
    padding: 1.2rem 1rem;
    text-align: center;
    color: #e0e0e0;
    height: 100%;
}
.metric-card .value {
    font-size: 2rem;
    font-weight: 700;
    color: #e94560;
    font-family: 'Playfair Display', serif;
    line-height: 1.1;
}
.metric-card .label {
    font-size: 0.72rem;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: #8892a4;
    margin-top: 0.3rem;
}
.section-title {
    font-family: 'Playfair Display', serif;
    font-size: 1.3rem;
    color: #1a1a2e;
    border-left: 4px solid #e94560;
    padding-left: 0.75rem;
    margin: 1.5rem 0 0.8rem;
}
footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ── Colores ───────────────────────────────────────────────────────────────────
RED    = "#e94560"
DARK   = "#1a1a2e"
BLUE   = "#0f3460"
GREEN  = "#53c28b"
ORANGE = "#f5a623"

LAYOUT_BASE = dict(
    font=dict(family="Source Sans 3, sans-serif", color="#2d2d2d"),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="#fafafa",
    margin=dict(t=40, b=40, l=40, r=20),
    hoverlabel=dict(bgcolor=DARK, font_color="white", font_size=13),
)

GENRE_COLORS = {
    "sci-fi": "#3a86ff", "fantasy": "#8338ec", "horror": "#e94560",
    "nonfiction": "#06d6a0", "biography": "#fb8500", "post-apocalyptic": "#ffb703",
    "hugo-award": "#ef476f", "favorites": "#ffd166", "political-theory": "#118ab2",
    "geopolitics": "#073b4c", "fulbo": "#2d6a4f", "vampire": "#9d0208",
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
    }
    df = df.rename(columns={k: v for k, v in col_map.items() if k in df.columns})

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


# ════════════════════════════════════════════════════════════════════════════
# HEADER
# ════════════════════════════════════════════════════════════════════════════
st.markdown("# 📚 Goodreads Explorer")
st.markdown("*Tu historial de lectura con zoom interactivo, ranking de autores y estadísticas detalladas.*")
st.divider()

# ── Sidebar: carga + filtros ──────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 📂 Cargar datos")
    uploaded = st.file_uploader(
        "CSV de Goodreads",
        type=["csv"],
        help="My Books → Import/Export → Export Library",
    )
    st.markdown("---")
    st.markdown(
        "**¿Cómo exportar?**\n\n"
        "1. Entrá a [goodreads.com](https://www.goodreads.com)\n"
        "2. My Books → Import/Export\n"
        "3. Export Library\n"
        "4. Subí el archivo acá ↑"
    )

if not uploaded:
    st.info("👈 Subí tu CSV de Goodreads desde el panel izquierdo para comenzar.")
    st.stop()

df = load_data(uploaded)

if df.empty:
    st.warning("No se encontraron libros marcados como 'read'.")
    st.stop()

# Sidebar filtros (después de cargar datos)
with st.sidebar:
    st.markdown("### 🔎 Filtros")

    # Año de lectura
    if df["read_year"].notna().any():
        yr_min, yr_max = int(df["read_year"].min()), int(df["read_year"].max())
        yr_range = st.slider("Año de lectura", yr_min, yr_max, (yr_min, yr_max))
    else:
        yr_range = None

    # Año de publicación
    if df["pub_year"].notna().any():
        pub_min = int(df["pub_year"].dropna().min())
        pub_max = int(df["pub_year"].dropna().max())
        pub_range = st.slider("Año de publicación", pub_min, pub_max, (pub_min, pub_max))
    else:
        pub_range = None

    # Géneros (todos los únicos)
    all_genres = sorted(set(g for lst in df["genre_list"] for g in lst if g))
    genres_sel = st.multiselect("Géneros", all_genres, default=all_genres)

    # Rating
    ratings_all = sorted(df["my_rating"].dropna().unique().tolist())
    ratings_sel = st.multiselect(
        "Mi rating ⭐",
        options=ratings_all,
        default=ratings_all,
        format_func=lambda x: f"{'⭐'*int(x)} ({int(x)})" if x > 0 else "Sin rating",
    )

# Aplicar filtros
mask = pd.Series([True] * len(df), index=df.index)
if yr_range:
    mask &= df["read_year"].between(*yr_range)
if pub_range:
    mask &= df["pub_year"].fillna(9999).between(*pub_range)
if genres_sel and len(genres_sel) < len(all_genres):
    mask &= df["genre_list"].apply(lambda lst: any(g in genres_sel for g in lst))
if ratings_sel is not None:
    mask &= df["my_rating"].isin(ratings_sel)

dff = df[mask].copy()

# ════════════════════════════════════════════════════════════════════════════
# MÉTRICAS GLOBALES
# ════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="section-title">Resumen</div>', unsafe_allow_html=True)
c1, c2, c3, c4, c5, c6 = st.columns(6)
metric_card(c1, f"{len(dff):,}", "Libros leídos")

total_pages = int(dff["pages"].sum(skipna=True))
metric_card(c2, f"{total_pages:,}", "Páginas totales")

metric_card(c3, dff["author"].nunique(), "Autores únicos")

rated = dff[dff["my_rating"] > 0]["my_rating"]
avg_r = rated.mean() if len(rated) else 0
metric_card(c4, f"{avg_r:.1f} ⭐", "Rating promedio")

top_author = dff["author"].value_counts().idxmax() if len(dff) else "—"
top_count  = dff["author"].value_counts().max() if len(dff) else 0
metric_card(c5, str(top_count), f"Más leído: {top_author.split(',')[0]}")

fav5 = len(dff[dff["my_rating"] == 5])
metric_card(c6, fav5, "Libros con 5 ⭐")

st.divider()

# ════════════════════════════════════════════════════════════════════════════
# TABS
# ════════════════════════════════════════════════════════════════════════════
tab1, tab2, tab3, tab4 = st.tabs([
    "🔭 Publicación vs Lectura",
    "👤 Autores",
    "📅 Historial & Páginas",
    "🏷️ Géneros & Rankings",
])


# ─────────────────────────────────────────────────────────────────────────────
# TAB 1: SCATTER interactivo
# ─────────────────────────────────────────────────────────────────────────────
with tab1:
    st.markdown(
        "Cada punto es un libro. **Zoom**: arrastrá un rectángulo con el mouse o usá la rueda. "
        "**Pan**: arrastrá con botón izquierdo luego de hacer zoom. "
        "**Reset**: doble clic."
    )

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
        rating_str = "⭐" * int(row.get("my_rating", 0)) if row.get("my_rating", 0) > 0 else "sin rating"
        pages_str  = f"{int(row['pages'])} págs" if pd.notna(row.get("pages")) else ""
        genre_str  = ", ".join(row.get("genre_list", []))
        parts = [
            f"<b>{row['title']}</b>",
            f"{row['author']}",
            f"Publicado: {int(row['pub_year'])}",
            f"Leído: {row['date_read'].strftime('%b %Y')}",
            f"{rating_str}",
        ]
        if pages_str:  parts.append(pages_str)
        if genre_str:  parts.append(genre_str)
        return "<br>".join(parts)

    scatter_df["hover"] = scatter_df.apply(hover_text, axis=1)

    # Construir un trace por cada género considerando TODOS los géneros del libro,
    # no solo el primero. Un libro con [sci-fi, favorites] aparece en ambos traces.
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
            title="Año de lectura",
            tickformat="d",
            gridcolor="#ebebeb",
            zeroline=False,
            range=[x_min, x_max],
        ),
        yaxis=dict(
            title="Año de publicación",
            gridcolor="#ebebeb",
            zeroline=False,
            range=[y_min, y_max],
        ),
        legend=dict(
            title="Géneros",
            orientation="v",
            bgcolor="rgba(255,255,255,0.9)",
            bordercolor="#ddd",
            borderwidth=1,
        ),
        dragmode="zoom",
        title="Año de publicación vs. año de lectura",
    )

    st.plotly_chart(fig, use_container_width=True)

    with st.expander("Ver tabla completa de libros"):
        cols_show = [c for c in ["title","author","pub_year","date_read","my_rating","pages","primary_genre"] if c in dff.columns]
        show_df = dff[cols_show].rename(columns={
            "title":"Título","author":"Autor","pub_year":"Publicado",
            "date_read":"Leído","my_rating":"Rating","pages":"Páginas",
            "primary_genre":"Género"
        }).sort_values("Leído", ascending=False)
        st.dataframe(show_df, use_container_width=True, height=320)


# ─────────────────────────────────────────────────────────────────────────────
# TAB 2: AUTORES
# ─────────────────────────────────────────────────────────────────────────────
with tab2:
    st.caption("💡 Hacé clic en una barra para ver los libros de ese autor.")
    top_n = st.slider("Mostrar top N", 5, 30, 15, key="top_n")

    col_a, col_b, col_c2 = st.columns(3)

    # ── Preparar los tres datasets ───────────────────────────────────────────
    auth_cnt = (
        dff["author"].value_counts().head(top_n)
        .reset_index().rename(columns={"count":"Libros","author":"Autor"})
    )

    auth_pag = (
        dff[dff["pages"].notna()]
        .groupby("author")["pages"].sum()
        .sort_values(ascending=False).head(top_n)
        .reset_index().rename(columns={"author":"Autor","pages":"Páginas"})
    )
    auth_pag["Páginas"] = auth_pag["Páginas"].astype(int)

    auth_rat = (
        dff[dff["my_rating"] > 0]
        .groupby("author")
        .agg(Libros=("title","count"), Rating=("my_rating","mean"))
        .query("Libros >= 2")
        .sort_values("Rating", ascending=False)
        .head(top_n).reset_index()
        .rename(columns={"author":"Autor"})
    )
    auth_rat["Rating"] = auth_rat["Rating"].round(2)

    chart_h = max(380, top_n * 28)

    with col_a:
        st.markdown('<div class="section-title">Por libros leídos</div>', unsafe_allow_html=True)
        fig_a = px.bar(auth_cnt, x="Libros", y="Autor", orientation="h",
                       color="Libros", color_continuous_scale=[BLUE, RED])
        fig_a.update_layout(**LAYOUT_BASE, height=chart_h,
                            yaxis=dict(autorange="reversed"), coloraxis_showscale=False)
        sel_a = st.plotly_chart(fig_a, use_container_width=True,
                                on_select="rerun", key="chart_authors_count")

    with col_b:
        st.markdown('<div class="section-title">Por páginas leídas</div>', unsafe_allow_html=True)
        fig_b2 = px.bar(auth_pag, x="Páginas", y="Autor", orientation="h",
                        color="Páginas", color_continuous_scale=[BLUE, GREEN])
        fig_b2.update_layout(**LAYOUT_BASE, height=chart_h,
                             yaxis=dict(autorange="reversed"), coloraxis_showscale=False)
        sel_b2 = st.plotly_chart(fig_b2, use_container_width=True,
                                 on_select="rerun", key="chart_authors_pages")

    with col_c2:
        st.markdown('<div class="section-title">Por rating promedio (≥2 libros)</div>', unsafe_allow_html=True)
        fig_b = px.bar(auth_rat, x="Rating", y="Autor", orientation="h",
                       color="Rating", color_continuous_scale=["#e94560", "#f5a623", "#53c28b"],
                       range_x=[0, 5.3], hover_data={"Libros": True})
        fig_b.update_layout(**LAYOUT_BASE, height=chart_h,
                            yaxis=dict(autorange="reversed"), coloraxis_showscale=False)
        sel_b = st.plotly_chart(fig_b, use_container_width=True,
                                on_select="rerun", key="chart_authors_rating")

    # ── Tabla al hacer clic ──────────────────────────────────────────────────
    selected_author = None

    for sel, df_ref, col_name in [
        (sel_a,  auth_cnt, "Autor"),
        (sel_b2, auth_pag, "Autor"),
        (sel_b,  auth_rat, "Autor"),
    ]:
        try:
            pts = sel.selection.get("points", [])
            if pts:
                idx = pts[0].get("point_index", None)
                if idx is not None:
                    selected_author = df_ref.iloc[idx][col_name]
                    break
        except Exception:
            pass

    if selected_author:
        st.markdown(f'<div class="section-title">📚 Libros de {selected_author}</div>', unsafe_allow_html=True)
        author_books = dff[dff["author"] == selected_author].copy()
        cols_show = [c for c in ["title","pub_year","date_read","my_rating","pages","primary_genre"] if c in author_books.columns]
        author_books = author_books[cols_show].rename(columns={
            "title":"Título","pub_year":"Publicado","date_read":"Leído",
            "my_rating":"Rating","pages":"Páginas","primary_genre":"Género"
        }).sort_values("Leído", ascending=False)
        if "Leído" in author_books.columns:
            author_books["Leído"] = author_books["Leído"].dt.strftime("%b %Y")
        if "Publicado" in author_books.columns:
            author_books["Publicado"] = author_books["Publicado"].fillna(0).astype(int)
        st.dataframe(author_books, use_container_width=True, hide_index=True)
    else:
        # Tabla resumen completa por defecto
        st.markdown('<div class="section-title">Detalle completo por autor</div>', unsafe_allow_html=True)
        agg = {"title": "count"}
        if "pages"     in dff.columns: agg["pages"]     = "sum"
        if "my_rating" in dff.columns: agg["my_rating"] = "mean"
        auth_table = (
            dff.groupby("author").agg(agg)
            .rename(columns={"title":"Libros","pages":"Páginas","my_rating":"Rating prom."})
            .sort_values("Libros", ascending=False).reset_index()
            .rename(columns={"author":"Autor"})
        )
        if "Rating prom." in auth_table.columns:
            auth_table["Rating prom."] = auth_table["Rating prom."].round(2)
        if "Páginas" in auth_table.columns:
            auth_table["Páginas"] = auth_table["Páginas"].fillna(0).astype(int)
        st.dataframe(auth_table, use_container_width=True, height=320)


# ─────────────────────────────────────────────────────────────────────────────
# TAB 3: HISTORIAL & PÁGINAS
# ─────────────────────────────────────────────────────────────────────────────
with tab3:
    st.caption("💡 Hacé clic en una barra para ver los libros de ese año o mes.")
    col_c, col_d = st.columns(2)

    MESES = ["Ene","Feb","Mar","Abr","May","Jun","Jul","Ago","Sep","Oct","Nov","Dic"]

    with col_c:
        st.markdown('<div class="section-title">Libros leídos por año</div>', unsafe_allow_html=True)
        by_yr = dff.groupby("read_year").size().reset_index(name="Libros").dropna()
        by_yr["read_year"] = by_yr["read_year"].astype(int)
        fig_yr = px.bar(by_yr, x="read_year", y="Libros",
                        color="Libros", color_continuous_scale=[BLUE, RED],
                        labels={"read_year":"Año"})
        fig_yr.update_layout(**LAYOUT_BASE, height=300, coloraxis_showscale=False)
        sel_yr = st.plotly_chart(fig_yr, use_container_width=True,
                                 on_select="rerun", key="chart_by_year")

    with col_d:
        st.markdown('<div class="section-title">Libros por mes (acumulado todos los años)</div>', unsafe_allow_html=True)
        by_mo = dff.groupby("read_month").size().reset_index(name="Libros").dropna()
        by_mo["Mes"] = by_mo["read_month"].apply(lambda x: MESES[int(x)-1])
        fig_mo = px.bar(by_mo, x="Mes", y="Libros",
                        color="Libros", color_continuous_scale=[BLUE, RED],
                        category_orders={"Mes": MESES})
        fig_mo.update_layout(**LAYOUT_BASE, height=300, coloraxis_showscale=False)
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
                selected_label = f"📅 Libros leídos en {yr_val}"
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
                    selected_label = f"📅 Libros leídos en {MESES[mo_val-1]}"
                    filtered_books = dff[dff["read_month"] == mo_val]
        except Exception:
            pass

    if filtered_books is not None and selected_label:
        st.markdown(f'<div class="section-title">{selected_label}</div>', unsafe_allow_html=True)
        cols_show = [c for c in ["title","author","date_read","my_rating","pages","primary_genre"] if c in filtered_books.columns]
        fb = filtered_books[cols_show].rename(columns={
            "title":"Título","author":"Autor","date_read":"Leído",
            "my_rating":"Rating","pages":"Páginas","primary_genre":"Género"
        }).sort_values("Leído", ascending=False)
        if "Leído" in fb.columns:
            fb["Leído"] = fb["Leído"].dt.strftime("%b %Y")
        st.dataframe(fb, use_container_width=True, hide_index=True)

    # Curva acumulada
    st.markdown('<div class="section-title">Libros acumulados a lo largo del tiempo</div>', unsafe_allow_html=True)
    cum = (
        dff.dropna(subset=["date_read"])
        .sort_values("date_read")
        .reset_index(drop=True)
    )
    cum["Acumulado"] = range(1, len(cum)+1)
    fig_cum = px.line(cum, x="date_read", y="Acumulado",
                      labels={"date_read":"Fecha"},
                      hover_data={"title": True} if "title" in cum.columns else {})
    fig_cum.update_traces(line_color=RED, line_width=2.5)
    fig_cum.update_layout(**LAYOUT_BASE, height=300)
    st.plotly_chart(fig_cum, use_container_width=True)

    # Páginas por año
    if "pages" in dff.columns:
        st.markdown('<div class="section-title">Páginas leídas por año</div>', unsafe_allow_html=True)
        pg_yr = dff.groupby("read_year")["pages"].sum().reset_index(name="Páginas").dropna()
        pg_yr["read_year"] = pg_yr["read_year"].astype(int)
        fig_pg = px.area(pg_yr, x="read_year", y="Páginas",
                         labels={"read_year":"Año"},
                         color_discrete_sequence=[RED])
        fig_pg.update_layout(**LAYOUT_BASE, height=280)
        st.plotly_chart(fig_pg, use_container_width=True)

    # ── Desglose mensual ─────────────────────────────────────────────────────
    st.divider()
    st.markdown('<div class="section-title">Desglose mensual</div>', unsafe_allow_html=True)
    st.caption("💡 Hacé clic en una barra para ver los libros de ese mes.")

    if dff["date_read"].notna().any():
        # Preparar columna Año-Mes para eje X
        monthly = dff.dropna(subset=["date_read"]).copy()
        monthly["anio_mes"] = monthly["date_read"].dt.to_period("M").astype(str)
        monthly["anio_mes_dt"] = pd.to_datetime(monthly["anio_mes"])

        col_m1, col_m2 = st.columns(2)

        with col_m1:
            st.markdown("**Libros por mes**")
            libros_mes = (
                monthly.groupby("anio_mes_dt").size()
                .reset_index(name="Libros")
                .sort_values("anio_mes_dt")
            )
            fig_lm = px.bar(libros_mes, x="anio_mes_dt", y="Libros",
                            color="Libros", color_continuous_scale=[BLUE, RED],
                            labels={"anio_mes_dt": "Mes"})
            fig_lm.update_layout(**LAYOUT_BASE, height=320,
                                 coloraxis_showscale=False,
                                 xaxis=dict(tickformat="%b %Y", tickangle=-45))
            sel_lm = st.plotly_chart(fig_lm, use_container_width=True,
                                     on_select="rerun", key="chart_libros_mes")

        with col_m2:
            if "pages" in monthly.columns:
                st.markdown("**Páginas por mes**")
                pags_mes = (
                    monthly.groupby("anio_mes_dt")["pages"].sum()
                    .reset_index(name="Páginas")
                    .sort_values("anio_mes_dt")
                )
                fig_pm = px.bar(pags_mes, x="anio_mes_dt", y="Páginas",
                                color="Páginas", color_continuous_scale=[BLUE, GREEN],
                                labels={"anio_mes_dt": "Mes"})
                fig_pm.update_layout(**LAYOUT_BASE, height=320,
                                     coloraxis_showscale=False,
                                     xaxis=dict(tickformat="%b %Y", tickangle=-45))
                sel_pm = st.plotly_chart(fig_pm, use_container_width=True,
                                         on_select="rerun", key="chart_pags_mes")
            else:
                sel_pm = None

        # Tabla al hacer clic en los gráficos mensuales
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
                        label_monthly = f"📅 Libros leídos en {mes_dt.strftime('%B %Y')}"
                        filtered_monthly = monthly[monthly["anio_mes_dt"] == mes_dt]
                        break
            except Exception:
                pass

        if filtered_monthly is not None and label_monthly:
            st.markdown(f'<div class="section-title">{label_monthly}</div>', unsafe_allow_html=True)
            cols_show = [c for c in ["title","author","date_read","my_rating","pages","primary_genre"] if c in filtered_monthly.columns]
            fm = filtered_monthly[cols_show].rename(columns={
                "title":"Título","author":"Autor","date_read":"Leído",
                "my_rating":"Rating","pages":"Páginas","primary_genre":"Género"
            }).sort_values("Leído", ascending=False)
            fm["Leído"] = fm["Leído"].dt.strftime("%d %b %Y")
            st.dataframe(fm, use_container_width=True, hide_index=True)


# ─────────────────────────────────────────────────────────────────────────────
# TAB 4: GÉNEROS & RANKINGS
# ─────────────────────────────────────────────────────────────────────────────
with tab4:
    st.caption("💡 Hacé clic en una barra para ver los libros de ese género, rating o década.")
    col_e, col_f = st.columns(2)

    # Preparar datos de década
    dec = dff.dropna(subset=["pub_year"]).copy()
    dec["Década"] = (dec["pub_year"] // 10 * 10).astype(int).astype(str) + "s"
    dec_cnt = dec.groupby("Década").size().reset_index(name="Libros").sort_values("Década")

    # Preparar datos de género
    exploded = dff.explode("genre_list").rename(columns={"genre_list":"Género"})
    exploded = exploded[exploded["Género"].notna() & (exploded["Género"] != "")]
    genre_cnt = exploded["Género"].value_counts().reset_index()
    genre_cnt.columns = ["Género","Libros"]

    with col_e:
        st.markdown('<div class="section-title">Libros por género</div>', unsafe_allow_html=True)
        fig_g = px.bar(
            genre_cnt, x="Libros", y="Género", orientation="h",
            color="Género", color_discrete_map=GENRE_COLORS,
        )
        fig_g.update_layout(
            **LAYOUT_BASE, height=max(300, len(genre_cnt)*26),
            yaxis=dict(autorange="reversed"), showlegend=False,
        )
        sel_genre = st.plotly_chart(fig_g, use_container_width=True,
                                    on_select="rerun", key="chart_genres")

    with col_f:
        st.markdown('<div class="section-title">Distribución de mis ratings</div>', unsafe_allow_html=True)
        rat_df = dff[dff["my_rating"] > 0]["my_rating"].value_counts().sort_index().reset_index()
        rat_df.columns = ["Rating","Cantidad"]
        rat_df["Estrellas"] = rat_df["Rating"].apply(lambda x: "⭐"*int(x))
        fig_rat = px.bar(rat_df, x="Estrellas", y="Cantidad",
                         color="Cantidad", color_continuous_scale=[ORANGE, RED])
        fig_rat.update_layout(**LAYOUT_BASE, height=300, coloraxis_showscale=False)
        sel_rat = st.plotly_chart(fig_rat, use_container_width=True,
                                  on_select="rerun", key="chart_ratings")

        st.markdown('<div class="section-title">Libros por década de publicación</div>', unsafe_allow_html=True)
        fig_dec = px.bar(dec_cnt, x="Década", y="Libros",
                         color="Libros", color_continuous_scale=[BLUE, RED])
        fig_dec.update_layout(**LAYOUT_BASE, height=280, coloraxis_showscale=False)
        sel_dec = st.plotly_chart(fig_dec, use_container_width=True,
                                  on_select="rerun", key="chart_decades")

    # ── Tabla al hacer clic ──────────────────────────────────────────────────
    selected_label = None
    filtered_books = None

    # Clic en género
    try:
        pts = sel_genre.selection.get("points", [])
        if pts:
            idx = pts[0].get("point_index", None)
            if idx is not None:
                genre_val = genre_cnt.iloc[idx]["Género"]
                selected_label = f"🏷️ Libros en el género: {genre_val}"
                filtered_books = dff[dff["genre_list"].apply(lambda lst: genre_val in lst)]
    except Exception:
        pass

    # Clic en rating
    if filtered_books is None:
        try:
            pts = sel_rat.selection.get("points", [])
            if pts:
                idx = pts[0].get("point_index", None)
                if idx is not None:
                    rat_val = int(rat_df.iloc[idx]["Rating"])
                    selected_label = f"⭐ Libros con {rat_val} estrella{'s' if rat_val != 1 else ''}"
                    filtered_books = dff[dff["my_rating"] == rat_val]
        except Exception:
            pass

    # Clic en década
    if filtered_books is None:
        try:
            pts = sel_dec.selection.get("points", [])
            if pts:
                idx = pts[0].get("point_index", None)
                if idx is not None:
                    dec_val = dec_cnt.iloc[idx]["Década"]
                    selected_label = f"📅 Libros publicados en los {dec_val}"
                    filtered_books = dec[dec["Década"] == dec_val]
        except Exception:
            pass

    if filtered_books is not None and selected_label:
        st.markdown(f'<div class="section-title">{selected_label}</div>', unsafe_allow_html=True)
        cols_show = [c for c in ["title","author","pub_year","date_read","my_rating","pages"] if c in filtered_books.columns]
        fb = filtered_books[cols_show].rename(columns={
            "title":"Título","author":"Autor","pub_year":"Publicado",
            "date_read":"Leído","my_rating":"Rating","pages":"Páginas"
        }).sort_values("Leído", ascending=False)
        if "Leído" in fb.columns:
            fb["Leído"] = fb["Leído"].dt.strftime("%b %Y")
        if "Publicado" in fb.columns:
            fb["Publicado"] = fb["Publicado"].fillna(0).astype(int)
        st.dataframe(fb, use_container_width=True, hide_index=True)

    # Rankings especiales (siempre visibles)
    st.markdown('<div class="section-title">🏆 Rankings especiales</div>', unsafe_allow_html=True)
    r1, r2, r3 = st.columns(3)

    with r1:
        st.markdown("**📖 Libros más largos**")
        if "pages" in dff.columns:
            longest = (
                dff.nlargest(8, "pages")[["title","author","pages"]]
                .dropna(subset=["pages"])
                .rename(columns={"title":"Título","author":"Autor","pages":"Págs"})
            )
            longest["Págs"] = longest["Págs"].astype(int)
            st.dataframe(longest, use_container_width=True, hide_index=True)

    with r2:
        st.markdown("**⭐ Tus 5 estrellas**")
        five_star = dff[dff["my_rating"] == 5][["title","author","read_year"]].rename(
            columns={"title":"Título","author":"Autor","read_year":"Año"}
        ).sort_values("Año", ascending=False)
        five_star["Año"] = five_star["Año"].fillna(0).astype(int)
        st.dataframe(five_star, use_container_width=True, hide_index=True)

    with r3:
        st.markdown("**📅 Últimos leídos**")
        recent = (
            dff.dropna(subset=["date_read"])
            .nlargest(10, "date_read")[["title","author","date_read","my_rating"]]
            .rename(columns={"title":"Título","author":"Autor","date_read":"Fecha","my_rating":"Rating"})
        )
        recent["Fecha"] = recent["Fecha"].dt.strftime("%b %Y")
        st.dataframe(recent, use_container_width=True, hide_index=True)
