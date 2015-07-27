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

from openerp import netsvc
from openerp.osv import osv, fields
from openerp.tools.translate import _

class pos_make_payment(osv.osv_memory):
    _inherit = 'pos.make.payment'
    
    def default_get(self, cr, uid, fields, context=None):
        res = super(pos_make_payment, self).default_get(cr, uid, fields, context=context)
        return res
    _columns = {
        #Thanh: set to required
        'payment_date': fields.datetime('Payment Date', required=True),
    }
    _defaults = {
        'payment_date': lambda *a: time.strftime('%Y-%m-%d %H:%M:%S'),
    }
    
    def fields_view_get(self, cr, uid, view_id=None, view_type=False, context=None, toolbar=False, submenu=False):
        journal_obj = self.pool.get('account.journal')
        if context is None:
            context = {}
        res = super(pos_make_payment,self).fields_view_get(cr, uid, view_id=view_id, view_type=view_type, context=context, toolbar=toolbar, submenu=submenu)
        
        #Thanh: Get Journal of Session
        if view_type == 'form':
            journal_ids = []
            session_id = context.get('pos_session_id', False) or False
    
            if session_id:
                session = self.pool.get('pos.session').browse(cr, uid, session_id, context=context)
                if session:
                    journal_ids = [journal.id for journal in session.config_id.journal_ids]
                
            for field in res['fields']:
                if field == 'journal_id' and type:
                    journal_select = journal_obj._name_search(cr, uid, '', [('id', 'in', journal_ids)], context=context, limit=None, name_get_uid=1)
                    res['fields'][field]['selection'] = journal_select
        return res
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
