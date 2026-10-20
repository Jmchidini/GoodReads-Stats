"""Cálculos compartidos, independientes de la interfaz."""


def rated_mean(ratings):
    """El cero representa un libro sin puntuación; no participa del promedio."""
    return ratings[ratings > 0].mean()


def sort_books(books, sort_col="date_read", ascending=False):
    """Orden estable, con valores desconocidos al final."""
    if sort_col not in books.columns:
        return books.copy()
    return books.sort_values(sort_col, ascending=ascending, na_position="last", kind="stable")
