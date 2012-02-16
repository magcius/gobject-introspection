#!/usr/bin/env python
# -*- Mode: Python -*-
# GObject-Introspection - a framework for introspecting GObject libraries
# Copyright (C) 2012 Jasper St. Pierre
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301, USA.
#

from .xmlwriter import XMLWriter

class BaseFormatter(object):
    def __init__(self):
        self.writer = None

class BaseWriter(object):
    def __init__(self, formatter):
        self._writer = XMLWriter()
        self._formatter = formatter
        self._transformer = None
        self.namespace = None

    def set_transformer(self, transformer):
        self._transformer = transformer
        self.namespace = self._transformer._namespace
