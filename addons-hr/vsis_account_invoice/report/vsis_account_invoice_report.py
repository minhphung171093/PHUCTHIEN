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

import time
from report import report_sxw
import pooler
from osv import osv
from tools.translate import _
import random
from datetime import datetime
from dateutil.relativedelta import relativedelta
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
DATE_FORMAT = "%Y-%m-%d"
import amount_to_text_vn
import amount_to_text_en

class Parser(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(Parser, self).__init__(cr, uid, name, context=context)
        self.user_obj = pooler.get_pool(self.cr.dbname).get('res.users')
        self.cr = cr
        self.uid = uid
        self.lead_planned_revenue = 0.0
        self.opp_planned_revenue = 0.0
        self.total_order = 0.0
        self.localcontext.update({
            'get_vietname_date':self.get_vietname_date,
            'amount_to_text':self.amount_to_text,
            'payment_type':self.payment_type,
            'tax_amount':self.tax_amount,
            'get_partner_address':self.get_partner_address,
            'get_day':self.get_day,
            'get_month':self.get_month,
            'get_year':self.get_year
        })

    
    def get_vietname_date(self, date):
        if not date:
            date = time.strftime(DATE_FORMAT)
        date = datetime.strptime(date, DATE_FORMAT)
        return date.strftime('%d-%m-%Y')
    
    def tax_amount(self, order):
        amount = 0
        if order.amount_untaxed > 0:
            amount = ((order.amount_total - order.amount_untaxed)/order.amount_untaxed)*100        
        return amount
    
    def get_partner_address(self, order):
        address = ''
        if order.partner_id:
            address += order.partner_id.street
            address += order.partner_id.street2 and ', '+ order.partner_id.street2 or ''
            address += order.partner_id.city and ', '+ order.partner_id.city or ''
            address += order.partner_id.state_id and ', ' + order.partner_id.state_id.name or ''
            address += order.partner_id.country_id and ', ' + order.partner_id.country_id.name or ''
        return address
    
    def amount_to_text(self, nbr, lang='vn', currency='USD'):
        if lang == 'vn':
            return  amount_to_text_vn.amount_to_text(nbr, lang)
        else:
            return amount_to_text_en.amount_to_text(nbr, 'en', currency)
    
    def payment_type(self,order):
        result = ''
        if order.partner_bank_id:
            result = 'Chuyen khoan'
        return result
    def get_day(self,order):
        result = 0
        if order.date_invoice:
            result = datetime.strptime(order.date_invoice, DATE_FORMAT).day
        return result
    def get_month(self,order):
        result = 0
        if order.date_invoice:
            result = datetime.strptime(order.date_invoice, DATE_FORMAT).month
        return result
    def get_year(self,order):
        result = 0
        if order.date_invoice:
            result = datetime.strptime(order.date_invoice, DATE_FORMAT).year % 2000
        return result
    

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

