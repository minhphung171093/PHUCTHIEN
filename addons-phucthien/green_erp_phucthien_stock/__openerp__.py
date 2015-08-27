# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
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
    'name': 'GreenERP Phuc Thien Stock',
    'version': '1.1',
    'category': 'GreenERP',
    "author" : "nguyentoanit@gmail.com",
    "website" : "http://incomtech.com.vn",
    'images': [],
    'depends': ['stock','general_stock','report_aeroo','green_erp_phucthien_sale','green_erp_phucthien_account','mail'],
    'data': [
            'security/green_erp_phucthien_stock_security.xml',
            'security/ir.model.access.csv',
            'report/phieu_xuat_kho.xml',
            'report/bien_ban_giao_nhan.xml',
            'report/dulieu_donghang_report_view.xml',
            'report/report_stock_move_view.xml',
            'report/bienban_kiemkho_thanhpham_view.xml',
            'report/bienban_kiemnhap_thuhoi_hangtrave_view.xml',
            'report/baocao_chenhlech_thuathieu_view.xml',
            'report/bienban_kiemkekho_view.xml',
            'report/phieu_dieuchuyen_noibo_view.xml',
            'report/ve_sinh_kho_view.xml',
            'report/suachua_hanhdong_view.xml',
            'stock_view.xml',
            'sequence.xml',
            'wizard/dulieu_donghang_report_view.xml',
            ],
    'demo': [],
    'test': [
    ],
    'installable': True,
    'auto_install': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
