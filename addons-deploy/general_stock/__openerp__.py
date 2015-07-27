# -*- coding: utf-8 -*-
##############################################################################
#
##############################################################################


{
    "name" : "General Stock",
    "version" : "7.0",
    "author" : "Le Truong Thanh <thanh.lt1689@gmail.com>",
    'category': 'General 70',
    "depends" : ["general_base","stock","sale_stock","purchase"],
    "init_xml" : [],
    "demo_xml" : [],
    "description": """
    """,
    'update_xml': [
        'security/ir.model.access.csv',
        'security/stock_security.xml',
        'report/report_view.xml',
        'wizard/stock_partial_picking_view.xml',
        'wizard/stock_onhand_report.xml',
        'wizard/stock_invoice_onshipping_view.xml',
        'wizard/stock_partial_move_view.xml',
        'wizard/stock_slip_picking_view.xml',
        
        'stock_view.xml',
        'wizard_stock_view.xml',
        'res_users_view.xml',
        'menu.xml',
        
    ],
    'test': [
    ],
    'installable': True,
    'auto_install': False,
    'certificate': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
