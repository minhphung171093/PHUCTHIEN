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

from osv import fields, osv
from tools.translate import _
from tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, float_compare

class stock_adjust_balance_value(osv.osv_memory):
    _name = 'stock.adjust.balance.value'
    _columns = {
        'date': fields.date('Date', required=True),
        'warehouse_id': fields.many2one('stock.warehouse','Warehouse',required=True),
        'stock_rule_id':fields.many2one('stock.default.rule','Stock Rule',required=True),
        'description':fields.char('Result',size=120,readonly=True)
    }
    
    _defaults = {
        'date': time.strftime(DEFAULT_SERVER_DATE_FORMAT),
    }
    
    def stock_adjust_balance(self, cr, uid, ids, context=None):
        adjust_balance = self.browse(cr,uid,ids[0])
        values ={}
        mess = False
        if adjust_balance:
            sql = '''
                select fn_stock_adjust_balance from fn_stock_adjust_balance('%s', %s, %s, %s)
            '''%(adjust_balance.date,adjust_balance.warehouse_id.id,adjust_balance.stock_rule_id.id,uid)
            cr.execute(sql)
            for line in cr.dictfetchall():
                mess = str(line['fn_stock_adjust_balance']) + ' Records Execute'
            if not mess:
                mess =  '0 Records Execute'
                
            data_obj = self.pool.get('ir.model.data')
            form_view_id = False
            view_ref = data_obj.get_object_reference(cr, uid, 'general_account', 'stock_adjust_balance_mess')
            form_view_id = view_ref and view_ref[1] or False,
            values = {'type': 'ir.actions.act_window_close'}
            context.update({'mess':mess})
            if form_view_id:
                values = {
                        'type':'ir.actions.act_window',
    #                    'domain': "[('id', 'in', ["+str(data{partial.picking_id.id})+"])]",
                        'name': 'Stock Adjust Balance Message',
                        'res_model':'stock.adjust.balance.mess',
                        'view_type': 'form',
                        'view_mode': 'form,tree',
                        #'res_id': data[partial.picking_id.id].get('delivered_picking',partial.picking_id.id),
                        'views': [(form_view_id[0],'form')],
                        'context':context,
                        'target': 'new',
                        'nodestroy': True,
                    }
        return values
stock_adjust_balance_value()

class stock_adjust_balance_mess(osv.osv_memory):
    _name = 'stock.adjust.balance.mess'
    _columns = {
        'description':fields.char('Result',size=120,readonly=True)
    }
    def default_get(self, cr, uid, fields, context=None):
        res = {}
        res = super(stock_adjust_balance_mess, self).default_get(cr, uid, fields, context=context)
        if context.get('mess',False):
            res.update({'description':context['mess']}) 
        return res
    _defaults = {
    }
stock_adjust_balance_mess()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
