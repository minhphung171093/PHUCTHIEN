# -*- encoding: utf-8 -*-
##############################################################################
#
#
##############################################################################

{
    "name" : "General Assets Management",
    "version" : "1.0",
    "depends" : ["account_asset","report_aeroo_ooo"],
    "author" : "Le Truong Thanh <thanh.lt1689@gmail.com>",
    "description": """Financial and accounting asset management.
    This Module manages the assets owned by a company or an individual. It will keep track of depreciation's occurred on
    those assets. And it allows to create Move's of the depreciation lines.
    """,
    "website" : "http://www.letruongthanh.com",
    "category" : "General 70",
    "sequence": 32,
    "init_xml" : [
    ],
    "demo_xml" : [ ],
    'test': [],
    "update_xml" : [
        'security/account_security.xml',
        'security/ir.model.access.csv',
        "wizard/account_asset_change_duration_view.xml",
        "wizard/wizard_asset_compute_view.xml",
        "wizard/print_report.xml",
        "report/report_view.xml",
        "report/account_asset_report_view.xml",
        "account_asset_view.xml",
        
        "menu.xml",
#        "account_asset_invoice_view.xml",
#        "report/account_asset_report_view.xml",
    ],
    "auto_install": False,
    "installable": True,
    "application": True,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

