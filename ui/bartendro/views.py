# -*- coding: utf-8 -*-
from bartendro.view import root, admin
from bartendro.view.admin import booze

view_map = {}
view_map['bartendro.view.root'] =  root
view_map['bartendro.view.admin'] =  admin
view_map['bartendro.view.admin.booze'] = booze
