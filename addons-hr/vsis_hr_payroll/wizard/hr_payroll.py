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

from openerp.osv import fields, osv
from openerp import netsvc
from openerp import pooler
from openerp.osv.orm import browse_record, browse_null
from openerp.tools.translate import _

class hr_payroll(osv.osv_memory):
    _name = "hr.payroll"
    _description = "Run payslip all"

    def fields_view_get(self, cr, uid, view_id=None, view_type='form',
                        context=None, toolbar=False, submenu=False):
        """
         Changes the view dynamically
         @param self: The object pointer.
         @param cr: A database cursor
         @param uid: ID of the user currently logged in
         @param context: A standard dictionary
         @return: New arch of view.
        """
        if context is None:
            context={}
        res = super(hr_payroll, self).fields_view_get(cr, uid, view_id=view_id, view_type=view_type, context=context, toolbar=toolbar,submenu=False)
        if context.get('active_model','') == 'hr.payslip' and len(context['active_ids']) < 2:
            raise osv.except_osv(_('Warning!'),
            _('Please select multiple order to run payslip in the list view.'))
        return res
    def run_payslip(self, cr, uid, ids, context=None):      
        slip_line_pool = self.pool.get('hr.payslip.line')
        slip_pool = self.pool.get('hr.payslip')
        sequence_obj = self.pool.get('ir.sequence')
        for line_payslip in context.get('active_ids',[]):                   
            payslip = slip_pool.browse(cr, uid, line_payslip, context=context)
            print payslip
            number = payslip.number or sequence_obj.get(cr, uid, 'salary.slip')
            old_slipline_ids = slip_line_pool.search(cr, uid, [('slip_id', '=', payslip.id)], context=context)
            if old_slipline_ids:
                slip_line_pool.unlink(cr, uid, old_slipline_ids, context=context)  
            if payslip.contract_id:
                contract_ids = [payslip.contract_id.id]
            else:                
                contract_ids = slip_pool.get_contract(cr, uid, payslip.employee_id, payslip.date_from, payslip.date_to, context=context)
            lines = [(0,0,line) for line in self.pool.get('hr.payslip').get_payslip_lines(cr, uid, contract_ids, payslip.id, context=context)]
            slip_pool.write(cr, uid, [payslip.id], {'line_ids': lines, 'number': number,}, context=context)
            print 'chay xuong day'
        return True
               

hr_payroll()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
