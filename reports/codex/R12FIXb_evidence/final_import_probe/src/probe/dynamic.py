def run(q):
    return getattr(q,"callback")(q)
