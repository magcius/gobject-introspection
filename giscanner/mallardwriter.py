#!/usr/bin/env python
# -*- Mode: Python -*-
# GObject-Introspection - a framework for introspecting GObject libraries
# Copyright (C) 2010 Zach Goldberg
# Copyright (C) 2011 Johan Dahlin
# Copyright (C) 2011 Shaun McCance
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

import os.path
import re

from . import ast
from .xmlwriter import XMLWriter
from .doctoolcommon import BaseFormatter, BaseWriter, Page, _space

XMLNS = "http://projectmallard.org/1.0/"
XMLNS_UI = "http://projectmallard.org/experimental/ui/"

class MallardFormatter(BaseFormatter):
    def get_method_as_title(self, entity):
        method = entity.get_ast()
        return "%s ()" % method.symbol

    def render_method(self, entity, link=False):
        method = entity.get_ast()
        self.writer.disable_whitespace()

        retval_type = method.retval.type
        if retval_type.ctype:
            link_dest = retval_type.ctype.replace("*", "")
        else:
            link_dest = str(retval_type)

        if retval_type.target_giname:
            ns = retval_type.target_giname.split('.')
            if ns[0] == self._namespace.name:
                link_dest = "%s" % (
                    retval_type.ctype.replace("*", ""))

        with self.writer.tagcontext("link", [("linkend", link_dest)]):
            self.writer.write_tag("returnvalue", [], link_dest)

        if retval_type.ctype is not None and '*' in retval_type.ctype:
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

class MallardPage(Page):
    def __init__(self, node, parent=None, root=None):
        super(MallardPage, self).__init__(node, parent, root)

        self.page_type = 'topic'
        self.page_style = ''

        self.title = self.root._formatter.get_title(self.node, parent)

        if not isinstance(node, ast.Namespace):
            if node.namespace is None:
                if parent is not None and parent.namespace is not None:
                    node.namespace = parent.namespace

        self.links = []
        self.linksels = []

        self.create_content()

    def add_link(self, linktype, xref, group=None):
        self.links.append((linktype, xref, group))

    def create_content(self):
        parent_id = self.parent.page_id

        if isinstance(self.node, ast.Namespace):
            self.page_type = 'guide'
            self.page_style = 'namespace'
            self.linksels = (('class', 'Classes'),
                             ('function', 'Functions'),
                             ('#first #default #last', 'Other'))
        elif isinstance(self.node, ast.Class):
            self.page_type = 'guide'
            self.page_style = 'class'
            self.linksels = (('constructor', 'Constructors'),
                             ('method', 'Methods'),
                             ('property', 'Properties'),
                             ('signal', 'Signals'),
                             ('#first #default #last', 'Other'))
            self.add_link('guide', parent_id, 'class')
        elif isinstance(self.node, ast.Record):
            self.page_type = 'guide'
            self.page_style = 'record'
            self.add_link('guide', parent_id)
        elif isinstance(self.node, ast.Interface):
            self.page_type = 'guide'
            self.page_style = 'interface'
            self.add_link('guide', parent_id)
        elif isinstance(self.node, ast.Function):
            if self.node.is_constructor:
                self.page_style = 'constructor'
                self.add_link('guide', parent_id, 'constructor')
            elif self.node.is_method:
                self.page_style = 'method'
                self.add_link('guide', parent_id, 'method')
            else:
                self.page_style = 'function'
                self.add_link('guide', parent_id, 'function')
        elif isinstance(self.node, ast.Property):
            self.page_style = 'property'
            self.add_link('guide', parent_id, 'property')
        elif isinstance(self.node, ast.Signal):
            self.page_style = 'signal'
            self.add_link('guide', parent_id, 'signal')

    def render(self, writer):
        with writer.tagcontext('page', [
            ('id', self.page_id),
            ('type', self.page_type),
            ('style', self.page_style),
            ('xmlns', XMLNS), ('xmlns:ui', XMLNS_UI)]):
            with writer.tagcontext('info'):
                for linktype, xref, group in self.links:
                    if group is not None:
                        writer.write_tag('link', [
                                ('type', linktype), ('xref', xref), ('group', group)])
                    else:
                        writer.write_tag('link', [
                                ('type', linktype), ('xref', xref)])
            writer.write_tag('title', [], self.title)
            if isinstance(self.node, ast.Annotated):
                self.render_doc(writer, self.node.doc)
            if isinstance(self.node, ast.Class):
                parent_chain = []
                node = self.node
                while node.parent:
                    node = self.root._transformer.lookup_giname(str(node.parent))
                    parent_chain.append(node)
                    if node.namespace.name == 'GObject' and node.name == 'Object':
                        break
                parent_chain.reverse()
                def print_chain(chain):
                    with writer.tagcontext('item', []):
                        attrs = []
                        title = self.root._formatter.get_title(chain[0], None)
                        if hasattr(chain[0], 'page'):
                            attrs.append(('xref', chain[0].page.page_id))
                        writer.write_tag('code', attrs, title)
                        if len(chain) > 1:
                            print_chain(chain[1:])
                with writer.tagcontext('synopsis', [('ui:expanded', 'no')]):
                    writer.write_tag('title', [], 'Hierarchy')
                    with writer.tagcontext('tree', []):
                        print_chain(parent_chain)
            for linkstype, title in self.linksels:
                with writer.tagcontext('links', [
                        ('type', 'topic'), ('ui:expanded', 'yes'),
                        ('groups', linkstype)]):
                    writer.write_tag('title', [], title)

    def render_doc(self, writer, doc):
        if doc is not None:
            for para in doc.split('\n\n'):
                writer.disable_whitespace()
                with writer.tagcontext('p', []):
                    self.render_doc_inline(writer, para)
                writer.enable_whitespace()

    def render_doc_inline(self, writer, text):
        poss = []
        poss.append((text.find('#'), '#'))
        poss = [pos for pos in poss if pos[0] >= 0]
        poss.sort(cmp=lambda x, y: cmp(x[0], y[0]))
        if len(poss) == 0:
            writer.write_line(text, do_escape=True)
        elif poss[0][1] == '#':
            pos = poss[0][0]
            writer.write_line(text[:pos], do_escape=True)
            rest = text[pos + 1:]
            link = re.split('[^a-zA-Z_:-]', rest, maxsplit=1)[0]
            xref = self.root.lookup_xref(link)
            writer.write_tag('link', [('xref', xref)], link)
            if len(link) < len(rest):
                self.render_doc_inline(writer, rest[len(link):])

class MallardWriter(BaseWriter):
    Page = MallardPage
    Formatter = MallardFormatter

    def write(self, output):
        xmlwriter = XMLWriter()
        self.root_page.render(xmlwriter)
        fp = open(output, 'w')
        fp.write(xmlwriter.get_xml())
        fp.close()

        for page in self.all_pages:
            xmlwriter = XMLWriter()
            page.render(xmlwriter)
            fp = open(os.path.join(os.path.dirname(output), page.page_id + '.page'), 'w')
            fp.write(xmlwriter.get_xml())
            fp.close()

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
