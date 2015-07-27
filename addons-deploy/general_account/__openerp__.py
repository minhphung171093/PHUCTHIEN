# -*- coding: utf-8 -*-
##############################################################################
#
##############################################################################


{
    "name" : "General Account",
    "version" : "6.1",
    "author" : "Le Truong Thanh <thanh.lt1689@gmail.com>",
    'category': 'General 70',
    "depends" : ["account","purchase","general_base"],
    "init_xml" : [],
    "demo_xml" : [],
    "description": """
    1) Add Discount Type into Invoice Line (Cash Discount) and Generating Discount Entry
    """,
    'update_xml': [
        "security/security.xml",
        "security/account_security.xml",
        "security/ir.model.access.csv",
       
        "menu.xml",
        "property_data.xml",
#         "project/project_view.xml",
#         "wizard/print_report.xml",
#         "wizard/account_use_model_view.xml",
#         "wizard/stock_adjust_balance_value.xml",
#         "wizard/account_reconcile_view.xml",
#         "report/report_view.xml",
#         "account_view.xml",
        "wizard/receivable_payable_reconciliation.xml",
        "account_invoice_view.xml",
        
        "account_view.xml",
        "master_account_view.xml",
        
    ],
    'test': [
    ],
    'installable': True,
    'auto_install': False,
    'certificate': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
