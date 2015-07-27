# -*- coding: utf-8 -*-
##############################################################################
#
##############################################################################

import logging
from datetime import datetime
from dateutil.relativedelta import relativedelta
from operator import itemgetter
import time

from openerp import SUPERUSER_ID
from openerp import pooler, tools
from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp.tools.float_utils import float_round
from lxml import etree

class invoice_book(osv.osv):
    _name="invoice.book"
    _columns={
        'name':fields.char('Tên sổ', size=128),
        'company_id':fields.many2one('res.company','Công ty',required=True),
        'kyhieuhoadon': fields.char('Ký hiệu hoá đơn', required=True),
        'mauhoadon': fields.char('Mẩu hoá đơn'),
        'sohoadon':fields.integer('Số kế tiếp', required=True),
        'tu_so':fields.integer('Từ số'),
        'den_so':fields.integer('Đến số'),
        'ngaymuaso': fields.date('Ngày mua sổ', required=True),
        'dodai':fields.char('Độ dài', required=True),
    }
    def create_sohoadonketiep(self,cr,uid,ids,context=None):
        this =self.browse(cr,uid,ids)
        number = '%%0%sd' % this.dodai % this.sohoadon
        sql ='''
            Update invoice_book set sohoadon = %s where id = %s
        '''%(this.sohoadon+1,ids)
        cr.execute(sql)
        return number
    
    _defaults = {
        'sohoadon': 1,
        'ngaymuaso': time.strftime('%Y-%m-%d'),
    }
    
invoice_book()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
