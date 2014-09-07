#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import

from . import services
from .services import Service
from .services import InvalidServiceError


__all__ = ['InvalidServiceError', 'Service']


__author__ = 'Patrick Carey, Lee Braiden'
__email__ = 'paddy@wackwack.co.uk, leebraid@gmail.com'
__version__ = '0.0.2'
