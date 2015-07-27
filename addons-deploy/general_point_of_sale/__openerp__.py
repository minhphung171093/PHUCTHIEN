# -*- coding: utf-8 -*-
##############################################################################
#
##############################################################################


{
    "name" : "General Point of Sale",
    "version" : "6.1",
    "author" : "Thanh",
    'category': 'General 70',
    "depends" : ["point_of_sale","report_aeroo","general_sale_team","general_account_voucher","general_account"],
    "init_xml" : [],
    "demo_xml" : [],
    "description": """
    """,
    'update_xml': [
          'security/ir.model.access.csv',
          'security/pos_security.xml',
          
          'wizard/group_bill.xml',
          'wizard/flag_update.xml',
          'wizard/bangke_point_of_sale.xml',
          'wizard/make_orders.xml',
          'wizard/pos_payment.xml',
          'wizard/line_update_view.xml',
          'report/report_view.xml',
          'point_of_sale_view.xml',
          'pos_view.xml',
          
    ],
    'test': [
    ],
    'installable': True,
    'auto_install': False,
    'certificate': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
