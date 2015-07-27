# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2012 ISA s.r.l. (<http://www.isa.it>).
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
import datetime

import netsvc
from osv import fields, osv
from tools.translate import _

class hr_overtime_batch(osv.osv):
    _name = "hr.overtime.batch"
    _description = "Overtime Batches"
    _order = "date_from asc"
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    
    def _compute_number_of_hours(self, cr, uid, ids, name, args, context=None):
        result = {}
        for hol in self.browse(cr, uid, ids, context=context):
              result[hol.id] = hol.number_of_hours_temp
        return result
    
    _columns = {
        'name': fields.char('Description', required=True, size=64),
        'create_uid':  fields.many2one('res.users', 'Creator', readonly=True),
        'rate': fields.float('Rate (%)', digits=(16,2), required=False, readonly=True, states={'draft':[('readonly',False)]}),
        
        'state': fields.selection([('draft', 'Draft'), ('confirm', 'Approval'), ('refuse', 'Refused')],
            'State', readonly=True),
        'date_from': fields.date('Start Date', readonly=True, states={'draft':[('readonly',False)]}),
        'date_to': fields.date('End Date', readonly=True, states={'draft':[('readonly',False)]}),
        'employee_ids': fields.many2many('hr.employee', 'overtime_batch_employee_rel', 'batch_id', 'employee_id', 'Employees', required=True),
        'manager_id': fields.many2one('hr.employee', 'Approver', readonly=True),
        'notes': fields.text('Reasons',readonly=True, states={'draft':[('readonly',False)]}),
        'number_of_hours_temp': fields.float('Number of Hours', readonly=True, states={'draft':[('readonly',False)]}),
        'number_of_hours': fields.function(_compute_number_of_hours, method=True, string='Number of Hours', store=True),
#         'manager_id2': fields.many2one('hr.employee', 'Second Approval', readonly=True, help='This area is automaticly filled by the user who validate the leave with second level (If Leave type need second validation)'),
        'overtime_type_id': fields.many2one("hr.overtime.type", "Overtime Type", required=True,readonly=True, states={'draft':[('readonly',False)]}),
#         'double_validation': fields.related('overtime_type_id', 'double_validation', type='boolean', relation='hr.overtime.type', string='Apply Double Validation'),
        
        'overtime_requests': fields.one2many('hr.overtime', 'batch_id', 'Overtime requests', readonly=True),
    }
    
    def _get_ot_type(obj, cr, uid, context=None):
        ids = obj.pool.get('hr.overtime.type').search(cr, uid, [], context=context)
        return ids and ids[0] or False
    
    _defaults = {
        'state': 'draft',
        'overtime_type_id': _get_ot_type,
    }
    _sql_constraints = [
        ('date_check', "CHECK ( number_of_hours_temp > 0 )", "The number of hours must be greater than 0 !"),
        ('date_check2', "CHECK (date_from <= date_to)", "The start date must be before the end date !")
    ]
    
    def onchange_overtime_type_id(self, cr, uid, ids, overtime_type_id):
        result = {}
        if not overtime_type_id:
            return {'value':{}}
        result['value'] = {
            'rate': self.pool.get('hr.overtime.type').browse(cr, uid, overtime_type_id).rate,
        }
        return result
    
    def unlink(self, cr, uid, ids, context=None):
        for rec in self.browse(cr, uid, ids, context=context):
            if rec.state not in ['draft','refuse']:
                raise osv.except_osv(_('Warning!'),_('You cannot delete a overtime which is not in draft state !'))
        return super(hr_overtime, self).unlink(cr, uid, ids, context)

    def onchange_date_from(self, cr, uid, ids, date_to, date_from):
        result = {}
        if not date_to:
            result['value'] = {
                'date_to': date_from,
            }
        return result
    
    def onchange_date_to(self, cr, uid, ids, date_to, date_from):
        result = {}
        result['value'] = {
#             'number_of_hours_temp': 0,
        }
        return result
    
    def set_to_draft(self, cr, uid, ids, context=None):
        ot = self.pool.get('hr.overtime')
        wf_service = netsvc.LocalService("workflow")
        for record in self.browse(cr, uid, ids, context=context):
            for line in record.overtime_requests:
                if line.state in ['refuse','cancel']:
                    wf_service.trg_create(uid, 'hr.overtime', line.id, cr)
        self.write(cr, uid, ids, {
            'state': 'draft',
            'manager_id': False,
        })
        return True

    def overtime_confirm(self, cr, uid, ids, context=None):
        ot = self.pool.get('hr.overtime')
        wf_service = netsvc.LocalService("workflow")
        for record in self.browse(cr, uid, ids, context=context):
            for employee in record.employee_ids:
                existing_ids = ot.search(cr, uid, [('employee_id','=',employee.id),('overtime_type_id','=',record.overtime_type_id.id),
                                    ('batch_id','=', record.id)])
                if not existing_ids:
                    vals = {
                            'name': record.name,
                            'employee_id': employee.id,
                            'overtime_type_id': record.overtime_type_id.id,
                            'rate': record.rate,
                            'date_from': record.date_from,
                            'date_to': record.date_to,
                            'number_of_hours_temp': record.number_of_hours_temp,
                            'notes': record.notes,
                            'batch_id': record.id,
                            }
                    ot_id = ot.create(cr, uid, vals)
                    wf_service.trg_validate(uid, 'hr.overtime', ot_id, 'validate', cr)
                    if record.overtime_type_id.double_validation:
                        wf_service.trg_validate(uid, 'hr.overtime', ot_id, 'second_validate', cr)
                else:
                    for ot_data in ot.browse(cr, uid, existing_ids):
                        if ot_data.state == 'confirm':
                            wf_service.trg_validate(uid, 'hr.overtime', ot_data.id, 'validate', cr)
                        if ot_data.state == 'validate1':
                            wf_service.trg_validate(uid, 'hr.overtime', ot_data.id, 'second_validate', cr)
        return self.write(cr, uid, ids, {'state': 'confirm'})
    
    def overtime_refuse(self, cr, uid, ids, context=None):
        ot = self.pool.get('hr.overtime')
        wf_service = netsvc.LocalService("workflow")
        for record in self.browse(cr, uid, ids, context=context):
            for line in record.overtime_requests:
                if line.state not in ['refuse','draft']:
                    wf_service.trg_validate(uid, 'hr.overtime', line.id, 'refuse', cr)
            self.write(cr, uid, [record.id], {'state': 'refuse'})
        return True
    
    def write(self, cr, uid, ids, vals, context=None):
        ot = self.pool.get('hr.overtime')
        update_ot_vals = {}
        fields = ['name','date_from','date_to','overtime_type_id','number_of_hours_temp','notes','rate']
        
        for field in fields:
            if field in vals:
                update_ot_vals[field] = vals[field]
        
        for record in self.browse(cr, uid, ids):
            ot_ids = [x.id for x in record.overtime_requests]
            if ot_ids:
                ot.write(cr, uid, ot_ids, update_ot_vals)
                
        return super(hr_overtime_batch,self).write(cr, uid, ids, vals, context=context)
    
hr_overtime_batch()
