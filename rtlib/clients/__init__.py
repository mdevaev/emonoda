from pkgutil import extend_path
__path__ = extend_path(__path__, __name__)

# TODO: Bullshit-fix for 3.2
# Setuptools: __init__.py does not call declare_namespace()! Please fix it.
# See /usr/lib/python3.4/site-packages/setuptools/command/build_py.py:176 for details
# ---> declare_namespace <---
