import os
from mininet.node import Controller
from mininet.log import info, error, warn, debug

pjoin = os.path.join

class POX(Controller):
  """ Controller to run POX """

  def __init__(self, name, *args, **kwargs):
    if 'modules' in kwargs:
      modules = kwargs['modules']
      del kwargs['modules']
    else:
      modules = []

    if 'POX_CORE_DIR' not in os.environ:
      error('exiting; please set missing POX_CORE_DIR env var\n')
      exit(1)
    poxCoreDir = os.environ['POX_CORE_DIR']

    command = pjoin(poxCoreDir, "pox.py")
    
    cargs = ['--verbose', 'openflow.of_01 --port=%d']
    cargs.extend(modules)
    cargs = ' '.join(cargs)
    
    
    cdir = poxCoreDir

    Controller.__init__(self, name, command=command, cargs=cargs, cdir=cdir, **kwargs)
