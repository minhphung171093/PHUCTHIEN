# -*- coding: utf-8 -*-
##############################################################################
#
##############################################################################


{
    "name" : "General Base",
    "version" : "6.1",
    "author" : "Le Truong Thanh <thanh.lt1689@gmail.com>",
    'category': 'General 70',
    "depends" : ["base","sale"],
    "init_xml" : [],
    "demo_xml" : [],
    "description": """
    1) Extend generating the Sequence
    """,
    'update_xml': [
        "security/security.xml",
        "res_address_view.xml",
        "res_partner_view.xml",
        "ir_sequence_view.xml",
        "res_users_view.xml",
        "res_payment_mode_data.xml",
        
        'menu.xml',
    ],
    'test': [
    ],
    'installable': True,
    'auto_install': False,
    'certificate': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
