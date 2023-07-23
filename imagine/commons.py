def general_get(q: str | None = None, page: int = 1, size: int = 10):
    return {"q": q, "page": page, "size": size}
