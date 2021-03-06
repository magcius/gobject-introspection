/* -*- mode: C; c-file-style: "gnu"; indent-tabs-mode: nil; -*-
 * GObject introspection: Interface
 *
 * Copyright (C) 2005 Matthias Clasen
 * Copyright (C) 2008,2009 Red Hat, Inc.
 *
 * This library is free software; you can redistribute it and/or
 * modify it under the terms of the GNU Lesser General Public
 * License as published by the Free Software Foundation; either
 * version 2 of the License, or (at your option) any later version.
 *
 * This library is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * Lesser General Public License for more details.
 *
 * You should have received a copy of the GNU Lesser General Public
 * License along with this library; if not, write to the
 * Free Software Foundation, Inc., 59 Temple Place - Suite 330,
 * Boston, MA 02111-1307, USA.
 */

#ifndef __GIINTERFACEINFO_H__
#define __GIINTERFACEINFO_H__

#if !defined (__GIREPOSITORY_H_INSIDE__) && !defined (GI_COMPILATION)
#error "Only <girepository.h> can be included directly."
#endif

#include <gitypes.h>

G_BEGIN_DECLS

#define GI_IS_INTERFACE_INFO(info) \
    (g_base_info_get_type((GIBaseInfo*)info) ==  GI_INFO_TYPE_INTERFACE)

gint             g_interface_info_get_n_prerequisites (GIInterfaceInfo *info);
GIBaseInfo *     g_interface_info_get_prerequisite    (GIInterfaceInfo *info,
						       gint             n);
gint             g_interface_info_get_n_properties    (GIInterfaceInfo *info);
GIPropertyInfo * g_interface_info_get_property        (GIInterfaceInfo *info,
						       gint             n);
gint             g_interface_info_get_n_methods       (GIInterfaceInfo *info);
GIFunctionInfo * g_interface_info_get_method          (GIInterfaceInfo *info,
						       gint             n);
GIFunctionInfo * g_interface_info_find_method         (GIInterfaceInfo *info,
						       const gchar     *name);
gint             g_interface_info_get_n_signals       (GIInterfaceInfo *info);
GISignalInfo *   g_interface_info_get_signal          (GIInterfaceInfo *info,
						       gint             n);
GIVFuncInfo *    g_interface_info_find_signal         (GIInterfaceInfo *info,
                                                       const gchar     *name);
gint             g_interface_info_get_n_vfuncs        (GIInterfaceInfo *info);
GIVFuncInfo *    g_interface_info_get_vfunc           (GIInterfaceInfo *info,
						       gint             n);
GIVFuncInfo *    g_interface_info_find_vfunc          (GIInterfaceInfo *info,
                                                       const gchar     *name);
gint             g_interface_info_get_n_constants     (GIInterfaceInfo *info);
GIConstantInfo * g_interface_info_get_constant        (GIInterfaceInfo *info,
						       gint             n);

GIStructInfo *   g_interface_info_get_iface_struct    (GIInterfaceInfo *info);

G_END_DECLS


#endif  /* __GIINTERFACEINFO_H__ */

