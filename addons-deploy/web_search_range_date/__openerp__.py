# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#
############################################################################

{
    'name': 'Web Search Range Date',
    'author' : 'thanhchatvn@gmail.com',
    'category' : 'Web',
    'website': 'http://www.besco.vn',
    'description': """
OpenErp Web Search range date time
============================
This is module add two form search all record from date and to date in form view data.
After install this, click any form data and testing it.
    """,
    'version': '1.0',
    'depends': ['web'],
    'data': [],
    'js': ['static/src/js/web_search_range_date.js'],
    'css': ['static/src/css/web_search_range_date.css'],
    'qweb' : [
        'static/src/xml/web_search_range_date.xml',
    ],

}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
