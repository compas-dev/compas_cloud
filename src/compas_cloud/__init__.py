from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import compas

from .proxy import Proxy

__version__ = '0.3.3rc0'

__all__ = ['Proxy']

__all_plugins__ = ['compas_cloud.install']

if not compas.IPY:
    from .sessions import Sessions

    __all__ += ['Sessions']
