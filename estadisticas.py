"""Cálculos compartidos, independientes de la interfaz."""


def rating_label(value):
    """Etiqueta numérica sin truncar decimales ni repetir estrellas enteras."""
    return f"{value:g} ⭐"


def rated_mean(ratings):
    """El cero representa un libro sin puntuación; no participa del promedio."""
    return ratings[ratings > 0].mean()


def rating_counts(ratings, show_all=False):
    """Cuenta puntuaciones; opcionalmente completa cuartos de estrella con ceros."""
    counts = ratings[ratings > 0].value_counts().sort_index()
    if show_all:
        # Conservar también puntuaciones observadas que no sean múltiplos de 0.25.
        scale = sorted(set(counts.index) | {step / 4 for step in range(1, 21)})
        counts = counts.reindex(scale, fill_value=0)
    return counts


def sort_books(books, sort_col="date_read", ascending=False):
    """Orden estable, con valores desconocidos al final."""
    if sort_col not in books.columns:
        return books.copy()
    return books.sort_values(sort_col, ascending=ascending, na_position="last", kind="stable")
