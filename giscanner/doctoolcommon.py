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

from . import ast
from .xmlwriter import XMLWriter

def _space(num):
    return " " * num

class LanguageSemanticsPython(object):
    def get_namespaced_node_title(self, node):
        return "%s.%s" % (node.namespace.name, node.name)

    def get_node_title(self, node, parent):
        if isinstance(node, ast.Namespace):
            return "%s Documentation" % node.name
        elif isinstance(node, ast.Function):
            if node.is_method or node.is_constructor:
                return "%s.%s.%s" % (node.namespace.name, parent.name, node.name)
            else:
                return "%s.%s" % (node.namespace.name, node.name)
        elif isinstance(node, ast.Property):
            return "%s" % node.name
        elif isinstance(node, ast.Signal):
            return "%s" % node.name
        else:
            return self.get_namespaced_node_title(node)

    def render_struct(self, node, writer):
        name = self.get_namespaced_node_title(node)

        parent = getattr(node, "parent", None)

        parent_name = ""
        if parent:
            if isinstance(node.parent, ast.Type):
                parent_name = str(node.parent)
            else:
                parent_name = self.get_namespaced_node_title(node)
        elif isinstance(node, ast.Interface):
            parent_name = "GObject.Interface"

        if parent_name:
            parent_clause = "(%s)" % (parent_name,)
        else:
            parent_clause = ""

        writer.write_line("%s%s:" % (name, parent_clause))

class LanguageSemanticsC(object):
    def get_node_title(self, node, parent):
        if isinstance(node, ast.Namespace):
            return "%s Documentation" % node.name
        elif isinstance(node, ast.Function):
            return node.symbol
        elif isinstance(node, ast.Property):
            return parent.c_name + ':' + node.name
        elif isinstance(node, ast.Signal):
            return parent.c_name + '::' + node.name
        else:
            return node.c_name

    def render_struct(self, node, writer):
        try:
            writer.disable_whitespace()
            writer.write_line("struct               ")
            writer.write_tag(
                "link",
                [("linkend", "%s-struct" % node.name)],
                "%s" % node.name)
            writer.write_line(";\n")
        finally:
            writer.enable_whitespace()

class BaseFormatter(object):
    def __init__(self, writer, language):
        self.writer = writer
        self.language = language

    def get_title(self, node, parent):
        return self.language.get_node_title(node, parent)

    def render_struct(self, node):
        self.language.render_struct(node, self.writer)

    def get_type_string(self, type):
        return str(type.ctype)

    def get_type_name(self, node):
        if isinstance(node, ast.Array):
            if node.array_type == ast.Array.C:
                return str(node.element_type) + "[]"
            else:
                return "%s&lt;%s&gt;" % (node.array_type, str(node.element_type))
        elif isinstance(node, ast.Map):
            return "GHashTable&lt;%s, %s&gt;" % (str(node.key_type), str(node.value_type))
        elif isinstance(node, ast.List):
            return "GList&lt;%s&gt;" % str(node.element_type)
        else:
            return str(node)

    def get_class_name(self, node):
        if node.gtype_name is None:
            return node.ctype
        return node.gtype_name

    def _render_parameter(self, param, extra_content=''):
        with self.writer.tagcontext("parameter"):
            if param.type.ctype is not None:
                link_dest = param.type.ctype.replace("*", "")
            else:
                link_dest = param.type.ctype
            with self.writer.tagcontext("link", [("linkend", "%s" % link_dest)]):
                self.writer.write_tag("type", [], link_dest)
            self.writer.write_line(extra_content)

    def _render_parameters(self, parent, parameters):
        self.writer.write_line(
            "%s(" % _space(40 - len(parent.symbol)))

        parent_class = parent.parent_class
        ctype = ast.Type(parent.parent_class.ctype + '*')
        params = []
        params.append(ast.Parameter(parent_class.name.lower(), ctype))
        params.extend(parameters)

        first_param = True
        for param in params:
            if not first_param:
                self.writer.write_line("\n%s" % _space(61))
            else:
                first_param = False

            if not param == params[-1]:
                comma = ", "
            else:
                comma = ""

            if isinstance(param.type, ast.Varargs):
                with self.writer.tagcontext("parameter"):
                    self.writer.write_line('...%s' % comma)
            else:
                extra_content = " "
                if param.type.ctype is not None and '*' in param.type.ctype:
                    extra_content += '*'
                extra_content += param.argname
                extra_content += comma
                self._render_parameter(param, extra_content)

        self.writer.write_line(");\n")

    def _get_annotations(self, argument):
        annotations = {}

        if hasattr(argument.type, 'element_type') and \
           argument.type.element_type is not None:
            if isinstance(argument.type.element_type, ast.Array):
                element_type = argument.type.element_type.array_type
            else:
                element_type = argument.type.element_type
            annotations['element-type'] = element_type

        if argument.transfer is not None and argument.transfer != 'none':
            annotations['transfer'] = argument.transfer

        if hasattr(argument, 'allow_none') and argument.allow_none:
            annotations['allow-none'] = None

        return annotations

class BaseWriter(object):
    def __init__(self, formatter, language):
        self._writer = XMLWriter()
        self._formatter = formatter(self._writer, language)
        self._transformer = None
        self.namespace = None

    def set_transformer(self, transformer):
        self._transformer = transformer
        self.namespace = self._transformer._namespace
