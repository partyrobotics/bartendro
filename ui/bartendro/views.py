# -*- coding: utf-8 -*-
from bartendro.view import root
from bartendro.view.admin import admin, booze
from bartendro.view.ws import booze as ws_booze

view_map = {}
view_map['bartendro.view.root'] =  root
view_map['bartendro.view.ws.booze'] =  ws_booze
view_map['bartendro.view.admin.admin'] =  admin
view_map['bartendro.view.admin.booze'] = booze
