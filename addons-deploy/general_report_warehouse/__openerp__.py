# -*- coding: utf-8 -*-
##############################################################################
#
#
##############################################################################

{
    "name" : "General Report Warehouse",
    "version" : "1.0",
    "author" : 'Pham Tuan Kiet <tykiet.208@gmail.com>',
    'complexity': "normal",
    "description": """
    """,
    "category": 'General 70',
    "sequence": 4,
    "website" : "",
    "images" : [],
    "depends" : ["stock","sale"],
    "init_xml" : [],
    "demo_xml" : [],
    "update_xml" : [
                    
        "report/report_view.xml",
        "wizard/stock_report.xml",
#         "wizard/export_file.xml",
        
#         "stock_transact_detail.xml",
#         "stock_onhand_analysis.xml",
#         "rep_product_list.xml",
        
        'menu.xml',
    ],
    "test" : [
    ],
    'certificate': False,
    "auto_install": False,
    "application": True,
    "installable": True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
