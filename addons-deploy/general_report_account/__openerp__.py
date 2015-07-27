# -*- coding: utf-8 -*-
##############################################################################
#
#
##############################################################################

{
    "name" : "Vietname Legal Reports",
    "version" : "7.0",
    "author" : 'Le Truong Thanh <thanh.lt1689@gmail.com>',
    'complexity': "normal",
    "description": """
    """,
    "category": 'General 70',
    "sequence": 4,
    "website" : "",
    "images" : [],
    "depends" : ["general_base","account_accountant","report_aeroo","report_aeroo_ooo","general_account_voucher","general_account_regularization"],
    "init_xml" : [],

    "demo_xml" : [],

    "update_xml" : [
        "report/report_view.xml",
        "wizard/print_report.xml",
        
#         "account_balance_sheet_report_template.xml",
        "menu.xml",
    ],
    "test" : [
    ],
    'certificate': False,
    "auto_install": False,
    "application": True,
    "installable": True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
