# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#    Copyright (C) 2011-2012 Serpent Consulting Services (<http://www.serpentcs.com>)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    "name" : "GreenERP Phuc Thien Account",
    "version" : "1.2",
    "author" : "nguyentoanit@gmail.com",
    "website" : "http://incomtech.com.vn",
    "category": "GreenERP",
    "complexity": "easy",
    "description": """
                    """,
    "depends" : ['account','green_erp_phucthien_sale','report_aeroo','general_account'],
    "demo" : [],
    "data" : [
            'wizard/doanhthu_banhang_view.xml',
            'report/hoadon_vat_view.xml',
            'report/doanhthu_banhang_report_view.xml',
            'account_view.xml',
        ],
  
    'test': [
    ],
    "installable": True,
    "auto_install": False,
    "application": True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
