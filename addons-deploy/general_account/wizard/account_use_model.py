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

class account_use_model(osv.osv_memory):

    _inherit = 'account.use.model'
    _columns = {
        'date': fields.date('Date', required=True)
    }
    
    _defaults = {
        'date': time.strftime(DEFAULT_SERVER_DATE_FORMAT),
    }
    
    def create_entries(self, cr, uid, ids, context=None):
        account_model_obj = self.pool.get('account.model')
        mod_obj = self.pool.get('ir.model.data')
        if context is None:
            context = {}
        data =  self.read(cr, uid, ids, context=context)[0]
        record_id = context and context.get('model_line', False) or False
        if record_id:
            model_ids = data['model']
        else:
            model_ids = context['active_ids']
        #Thanh: add wizard.date to context to generate Move
        context['date'] = data['date']
        
        move_ids = account_model_obj.generate(cr, uid, model_ids, context=context)
        
        context.update({'move_ids':move_ids})
        model_data_ids = mod_obj.search(cr, uid,[('model','=','ir.ui.view'),('name','=','view_move_form')], context=context)
        resource_id = mod_obj.read(cr, uid, model_data_ids, fields=['res_id'], context=context)[0]['res_id']
        return {
            'domain': "[('id','in', ["+','.join(map(str,context['move_ids']))+"])]",
            'name': 'Entries',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.move',
            'views': [(False,'tree'),(resource_id,'form')],
            'type': 'ir.actions.act_window',
        }

account_use_model()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
