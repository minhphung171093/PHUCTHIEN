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
from openerp.tools.translate import _
from datetime import datetime

class hr_attendance(osv.osv):
    _inherit = "hr.attendance"
    
    def _get_user_department(self, cr, uid, ids, field_name, arg, context=None):
        employee_pool = self.pool.get('hr.employee')
        res = {}
        for attendance in self.browse(cr, uid, ids, context=context):
            res[attendance.id] = attendance.employee_id.department_id and attendance.employee_id.department_id.id or False
        return res
    
    def _compute_date_user_tz(self, cr, uid, ids, fieldnames, args, context=None):
        user_pool = self.pool.get('res.users')
        res = {}
        for obj in self.browse(cr, uid, ids, context=context):
            res[obj.id] = {
                'date_user_tz': False,
                'day_user_tz': False,
            }
            
            date_user_tz = user_pool._convert_user_datetime(cr, obj.employee_id and obj.employee_id.user_id.id or uid, obj.name)
            res[obj.id]['date_user_tz'] = date_user_tz.strftime('%Y-%m-%d')
            res[obj.id]['day_user_tz'] = date_user_tz.strftime('%d-%m-%Y')
        return res
    
    _columns = {
        'department_id': fields.function(_get_user_department, type='many2one', relation='hr.department', string='Department',
            store={
                'hr.attendance': (lambda self, cr, uid, ids, c={}: ids, ['employee_id'], 10),
            }, readonly=True),
                
        'date_user_tz': fields.function(_compute_date_user_tz, type='date', method=True, string='Date User TZ', store={
                'hr.attendance': (lambda self, cr, uid, ids, c={}: ids, ['name'], 10),
            }, multi='tz'),
        
        'day_user_tz': fields.function(_compute_date_user_tz, type='char', method=True, string='Day User TZ', store={
                'hr.attendance': (lambda self, cr, uid, ids, c={}: ids, ['name'], 10),
            }, multi='tz'),
                
        'notes': fields.text('Notes'),
    }
    
    _defaults = {
    }
    
    def search(self, cr, uid, args, offset=0, limit=None, order=None,
            context=None, count=False):
        if context is None:
            context = {}

        return super(hr_attendance, self).search(cr, uid, args, offset, limit,
                order, context=context, count=count)
hr_attendance()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
