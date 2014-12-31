import os, IPython

os.environ['PYTHONSTARTUP'] = os.path.join(os.environ['HW_PREFIX'], 'initialize.py')

IPython.start_ipython()
raise SystemExit
