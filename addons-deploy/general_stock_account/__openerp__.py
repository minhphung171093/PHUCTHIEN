# -*- coding: utf-8 -*-
##############################################################################
#
##############################################################################


{
    "name" : "General Stock Account",
    "version" : "7.0",
    "author" : "Kiet pham <tykiet.208@com>",
    'category': 'General 70',
    "depends" : ["general_stock","general_report_warehouse"],
    "init_xml" : [],
    "demo_xml" : [],
    "description": """
    """,
    'update_xml': [
        'security/ir.model.access.csv',
        'security/security.xml',
        
        'cost_history_view.xml',
        'menu.xml',
    ],
    'test': [
    ],
    'installable': True,
    'auto_install': False,
    'certificate': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
