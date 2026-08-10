"""Vendored copy of serving/app's model-loading modules for the Railway demo.

config.py, model_loader.py, preprocessing.py, and schemas.py are reused
as-is from serving/app (not reimplemented). They're copied rather than
imported across a package boundary so this folder stays a single,
self-contained Railway build root -- the same reason demo/app/ exists
alongside demo/main.py. preprocessing.py in particular must live at this
exact "app.preprocessing" module path: the joblib artifact pickles a
reference to clean_text by that path, so unpickling requires an
importable module named app.preprocessing here too.
"""
