#!/usr/bin/env python
# -*- Mode: Python -*-
# GObject-Introspection - a framework for introspecting GObject libraries
# Copyright (C) 2010 Zach Goldberg
# Copyright (C) 2011 Johan Dahlin
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
from .doctoolcommon import BaseFormatter, BaseWriter, _space
from .docbookdescription import get_formatted_description

XMLNS = "http://docbook.org/ns/docbook"
XMLVERSION = "5.0"
DOCTYPE = """<!DOCTYPE refentry PUBLIC "-//OASIS//DTD DocBook XML V4.1.2//EN"
               "http://www.oasis-open.org/docbook/xml/4.1.2/docbookx.dtd" [
<!ENTITY % local.common.attrib "xmlns:xi  CDATA  #FIXED 'http://www.w3.org/2003/XInclude'">
<!ENTITY version SYSTEM "version.xml">
]>""" #"

class DocBookFormatter(BaseFormatter):
    def get_method_as_title(self, method):
        return "%s ()" % method.symbol

    def get_page_name(self, node):
        # page name is only used for xml:id (not displayed to users)
        if isinstance(node, ast.Alias) or node.gtype_name is None:
            return node.ctype
        return node.gtype_name

    def render_method(self, method, link=False):
        self.writer.disable_whitespace()

        retval_type = method.retval.type
        if retval_type.ctype:
            link_dest = retval_type.ctype.replace("*", "")
        else:
            link_dest = str(retval_type)

        if retval_type.target_giname:
            ns = retval_type.target_giname.split('.')
            if ns[0] == self.namespace.name:
                link_dest = "%s" % (
                    retval_type.ctype.replace("*", ""))

        with self.writer.tagcontext("link", [("linkend", link_dest)]):
            self.writer.write_tag("returnvalue", [], link_dest)

        if '*' in retval_type.ctype:
            self.writer.write_line(' *')

        self.writer.write_line(
            _space(20 - len(self.get_type_string(method.retval.type))))

        if link:
            self.writer.write_tag("link", [("linkend",
                                            method.symbol.replace("_", "-"))],
                                  method.symbol)
        else:
            self.writer.write_line(method.symbol)

        self._render_parameters(method, method.parameters)
        self.writer.enable_whitespace()

    def render_param_list(self, method):
        self._render_param(method.parent_class.name.lower(), 'instance', [])

        for param in method.parameters:
            if isinstance(param.type, ast.Varargs):
                argname = '...'
            else:
                argname = param.argname
            self._render_param(argname, param.doc, self._get_annotations(param))

        self._render_param('Returns', method.retval.doc,
                           self._get_annotations(method.retval))

    def _render_param(self, argname, doc, annotations):
        with self.writer.tagcontext('varlistentry'):
            with self.writer.tagcontext('term'):
                self.writer.disable_whitespace()
                try:
                    with self.writer.tagcontext('parameter'):
                        self.writer.write_line(argname)
                    if doc is not None:
                        self.writer.write_line('&#xA0;:')
                finally:
                    self.writer.enable_whitespace()
            if doc is not None:
                with self.writer.tagcontext('listitem'):
                    with self.writer.tagcontext('simpara'):
                        self.writer.write_line(doc)
                        if annotations:
                            with self.writer.tagcontext('emphasis', [('role', 'annotation')]):
                                for key, value in annotations.iteritems():
                                    self.writer.disable_whitespace()
                                    try:
                                        self.writer.write_line('[%s' % key)
                                        if value is not None:
                                            self.writer.write_line(' %s' % value)
                                        self.writer.write_line(']')
                                    finally:
                                        self.writer.enable_whitespace()

    def render_property(self, prop, link=False):
        prop_name = '"%s"' % prop.name
        prop_type = self.get_type_name(prop.type)

        flags = []
        if prop.readable:
            flags.append("Read")
        if prop.writable:
            flags.append("Write")
        if prop.construct:
            flags.append("Construct")
        if prop.construct_only:
            flags.append("Construct Only")

        self._render_prop_or_signal(prop_name, prop_type, flags)

    def _render_prop_or_signal(self, name, type_, flags):
        self.writer.disable_whitespace()

        line = _space(2) + name + _space(27 - len(name))
        line += str(type_) + _space(22 - len(str(type_)))
        line += ": " + " / ".join(flags)

        self.writer.write_line(line + "\n")

        self.writer.enable_whitespace()


    def render_signal(self, signal, link=False):
        sig_name = '"%s"' % signal.name

        flags = []
        if signal.when == "first":
            flags.append("Run First")
        elif signal.when == "last":
            flags.append("Run Last")
        elif signal.when == "cleanup":
            flags.append("Cleanup")

        if signal.no_recurse:
            flags.append('No Recursion')
        if signal.detailed:
            flags.append("Has Details")
        if signal.action:
            flags.append("Action")
        if signal.no_hooks:
            flags.append("No Hooks")

        self._render_prop_or_signal(sig_name, "", flags)

class DocBookPage(object):
    def __init__(self, name, ast_node):
        self.methods = []
        self.properties = []
        self.signals = []
        self.name = name
        self.description = ast_node.doc
        self.ast = ast_node
        self.id = None

        if isinstance(ast_node, (ast.Class, ast.Record, ast.Interface)):
            for method in ast_node.methods:
                method.parent_class = ast_node
            self.methods = ast_node.methods

        if isinstance(ast_node, (ast.Class, ast.Interface)):
            self.properties = ast_node.properties
            self.signals = ast_node.signals

    def get_methods(self):
        return self.methods

    def get_properties(self):
        return self.properties

    def get_signals(self):
        return self.signals

class DocBookWriter(BaseWriter):
    def __init__(self, language):
        super(DocBookWriter, self).__init__(DocBookFormatter, language)
        self._pages = []

    def _add_page(self, page):
        self._pages.append(page)

    def set_transformer(self, transformer):
        super(DocBookWriter, self).set_transformer(transformer)
        self._formatter.namespace = self.namespace
        for name, node in self.namespace.iteritems():
            if isinstance(node, (ast.Class, ast.Record, ast.Interface, ast.Alias)):
                page_name = self._formatter.get_page_name(node)
                self._add_node(node, page_name)

    def _add_node(self, node, name):
        page = DocBookPage(name, node)
        self._add_page(page)

        if isinstance(node, (ast.Class, ast.Record, ast.Interface, ast.Alias)):
            page.id = node.ctype

    def write(self, output):
        self._writer.write_line(DOCTYPE)
        with self._writer.tagcontext("book", [
            ("xml:id", "page_%s" % self.namespace.name),
            ("xmlns", XMLNS),
            ("version", XMLVERSION)]):
            self._writer.write_tag("title", [], "%s Documentation" % (
                self.namespace.name))

            for page in self._pages:
                self._render_page(page)

        fp = open(output, 'w')
        fp.write(self._writer.get_xml())
        fp.close()

    def _render_page(self, page):
        with self._writer.tagcontext("chapter", [("xml:id", "ch_%s" % (
                        page.name))]):
            self._writer.write_tag(
                "title", [], self._formatter.get_title(page.ast, None))

            with self._writer.tagcontext("refsynopsisdiv",
                    [('id', '%s.synopsis' % page.name),
                     ('role', 'synopsis')]):

                self._writer.write_tag(
                    "title", [("role", "synopsis.title")], "Synopsis")

                if not isinstance(page.ast, ast.Alias):
                    self._writer.write_tag("anchor", [("id", page.name)])

                with self._writer.tagcontext('synopsis'):
                    self._formatter.render_struct(page.ast)

                    for ast_node in page.get_methods():
                        self._formatter.render_method(ast_node, link=True)

            if isinstance(page.ast, (ast.Class, ast.Interface)):
                with self._writer.tagcontext("refsect1",
                                            [('id', '%s.object-hierarchy' % page.name),
                                             ('role', 'object_hierarchy')]):
                    self._writer.write_tag('title', [('role', 'object_hierarchy.title')],
                                          "Object Hierarchy")
                    with self._writer.tagcontext('synopsis'):
                        self._render_page_object_hierarchy(page.ast)

            if page.get_properties():
                with self._writer.tagcontext('refsect1',
                                            [('id', '%s.properties' % page.name),
                                             ('role', 'properties')]):
                    self._writer.write_tag("title", [('role', 'properties.title')],
                                          "Properties")
                    with self._writer.tagcontext("synopsis"):
                        for ast_node in page.get_properties():
                            if isinstance(ast_node.type, ast.TypeUnknown):
                                print "Warning: ignoring property '%s' for " \
                                      "lack of type" % ast_node.name
                                continue
                            self._formatter.render_property(ast_node, link=True)

            if page.get_signals():
                with self._writer.tagcontext('refsect1',
                                            [('id', '%s.signals' % page.name),
                                             ('role', 'signal_proto')]):
                    self._writer.write_tag('title', [('role', 'signal_proto.title')],
                                          "Signals")
                    with self._writer.tagcontext('synopsis'):
                        for ast_node in page.get_signals():
                            self._formatter.render_signal(ast_node, link=True)

            if page.description:
                with self._writer.tagcontext('refsect1',
                                            [('id', '%s.description' % (page.name, ))]):
                    self._writer.write_tag(
                        "title", [("role", "desc.title")], "Description")
                    self._render_description(page.description)

            with self._writer.tagcontext('refsect1',
                                        [('id', "%s-details" % page.id.lower()),
                                         ("role", "details")]):
                self._writer.write_tag("title", [("role", "details.title")],
                                      "Details")

                if isinstance(page.ast, ast.Alias):
                    self._render_alias_detail(page.ast)
                else:
                    self._render_struct_detail(page.ast)

                for ast_node in page.get_methods():
                    self._render_method(ast_node)

            if page.get_properties():
                with self._writer.tagcontext('refsect1',
                                            [('id', '%s.property-details' % page.name),
                                             ('role', 'property_details')]):
                    self._writer.write_tag('title', [('role', 'property_details.title')],
                                           "Property Details")
                    for ast_node in page.get_properties():
                        self._render_property(ast_node)

            if page.get_signals():
                with self._writer.tagcontext('refsect1',
                                            [('id', '%s.signal-details' % page.name),
                                             ('role', 'signals')]):
                    self._writer.write_tag('title', [('role', 'signal.title')],
                                           "Signal Details")
                    for ast_node in page.get_signals():
                        self._render_signal(ast_node)

    def _render_alias_detail(self, alias):
        with self._writer.tagcontext('refsect2',
                              [('id', "%s" % alias.ctype),
                               ('role', 'typedef')]):
            self._writer.write_tag("title", [], "%s" % alias.ctype)
            with self._writer.tagcontext("indexterm", [("zone", "%s" % alias.ctype)]):
                self._writer.write_tag("primary", [("sortas", alias.name)], alias.ctype)
            self._writer.write_tag("programlisting",
                                   [],
                                   "typedef %s %s" % (alias.target.ctype,
                                                      alias.ctype))
            self._writer.write_tag("para", [], alias.doc)

    def _render_struct_detail(self, struct):
        with self._writer.tagcontext('refsect2',
                              [('id', "%s-struct" % struct.ctype),
                               ('role', 'struct')]):
            self._writer.write_tag("title", [], "struct %s" % struct.ctype)
            with self._writer.tagcontext("indexterm", [("zone", "%s-struct" % struct.ctype)]):
                self._writer.write_tag("primary", [("sortas", struct.name)], struct.ctype)
            self._writer.write_tag("programlisting", [], "struct %s;" % struct.ctype)

    def _render_method(self, ast_node):

        link_name = ast_node.symbol.replace("_", "-")

        self._writer.push_tag('refsect2',
                              [('id', link_name),
                               ('role', 'function')])
        self._writer.write_tag("title", [],
                               self._formatter.get_method_as_title(ast_node))

        with self._writer.tagcontext("indexterm", [("zone", link_name)]):
            self._writer.write_tag("primary", [], ast_node.name)

        with self._writer.tagcontext("programlisting"):
            self._formatter.render_method(ast_node)

        description = ast_node.doc
        if description:
            self._render_description(ast_node.doc)

        with self._writer.tagcontext("variablelist", [("role", "params")]):
            self._formatter.render_param_list(ast_node)

        self._writer.pop_tag()

    def _render_property(self, ast_node):
        self._writer.write_line("Not implemented yet")

    def _render_signal(self, ast_node):
        self._writer.write_line("Not implemented yet")

    def _render_page_object_hierarchy(self, page_node):
        parent_chain = self._get_parent_chain(page_node)
        parent_chain.append(page_node)
        lines = []

        for level, parent in enumerate(parent_chain):
            prepend = ""
            if level > 0:
                prepend = _space((level - 1)* 6) + " +----"
            lines.append(_space(2) + prepend + self._formatter.get_class_name(parent))

        self._writer.disable_whitespace()
        self._writer.write_line("\n".join(lines))
        self._writer.enable_whitespace()

    def _render_description(self, description):
        formatted_desc = get_formatted_description(description)
        self._writer.write_line(formatted_desc)

    def _get_parent_chain(self, page_node):
        parent_chain = []

        node = page_node
        while node.parent and node.gi_name != 'GObject.Object':
            node = self._transformer.lookup_giname(str(node.parent))
            parent_chain.append(node)

        parent_chain.reverse()
        return parent_chain
