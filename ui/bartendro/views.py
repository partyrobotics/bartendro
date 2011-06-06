# -*- coding: utf-8 -*-
from bartendro.view import root
from bartendro.view.admin import admin, booze

view_map = {}
view_map['bartendro.view.root'] =  root
view_map['bartendro.view.admin.admin'] =  admin
view_map['bartendro.view.admin.booze'] = booze
