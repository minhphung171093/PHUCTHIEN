# -*- coding: utf-8 -*-
##############################################################################
#
##############################################################################


{
    "name" : "General Stock Inventory",
    "version" : "7.0",
    "author" : "Le Truong Thanh <thanh.lt1689@gmail.com>",
    'category': 'General 70',
    "depends" : ["general_stock","general_base","report_aeroo","report_aeroo_ooo"],
    "init_xml" : [],
    "demo_xml" : [],
    "description": """
    """,
    'update_xml': [
        'stock_inventory.xml',
        'report/report_view.xml'
    ],
    'test': [
    ],
    'installable': True,
    'auto_install': False,
    'certificate': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
