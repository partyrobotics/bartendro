# -*- coding: utf-8 -*-
from bartendro.view import root
from bartendro.view.admin import admin, booze as booze_admin, drink as drink_admin, dispenser as admin_dispenser
from bartendro.view.drink import drink
from bartendro.view.ws import booze as ws_booze, dispenser as ws_dispenser, drink as ws_drink, misc as ws_misc

view_map = {}
view_map['bartendro.view.root'] =  root
view_map['bartendro.view.ws.booze'] =  ws_booze
view_map['bartendro.view.admin.admin'] =  admin
view_map['bartendro.view.admin.booze'] = booze_admin
view_map['bartendro.view.admin.drink'] = drink_admin
view_map['bartendro.view.admin.dispenser'] = admin_dispenser
view_map['bartendro.view.ws.dispenser'] = ws_dispenser
view_map['bartendro.view.ws.drink'] = ws_drink
view_map['bartendro.view.ws.misc'] = ws_misc
view_map['bartendro.view.drink.drink'] = drink
