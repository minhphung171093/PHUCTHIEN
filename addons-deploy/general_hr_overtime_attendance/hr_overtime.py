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

class hr_overtime(osv.osv):
    _inherit = "hr.overtime"
    
    def _get_attendances(self, cr, uid, ids, name, args, context=None):
        result = {}
        user_pool = self.pool.get('res.users')
        for ho in self.browse(cr, uid, ids, context=context):
            usertz_vs_utctz = user_pool.get_diff_hours_usertz_vs_utctz(cr, ho.employee_id.user_id.id or uid) or 7
            lines = []
            result.setdefault(ho.id, {
                'attendances_ids': lines,
            })
            cr.execute("""
                    SELECT a.id
                      FROM hr_attendance a
                    WHERE   a.action = 'sign_in'
                            AND %(date_to)s >= (a.name + interval '%(usertz_vs_utctz)s hour')::date
                            AND %(date_from)s <= (a.name + interval '%(usertz_vs_utctz)s hour')::date
                            AND %(employee_id)s = a.employee_id
                     GROUP BY a.id""", {'date_from': ho.date_from,
                                        'date_to': ho.date_to,
                                        'usertz_vs_utctz': usertz_vs_utctz,
                                        'employee_id': ho.employee_id.id,})
            lines.extend([row[0] for row in cr.fetchall()])
            result[ho.id]['attendances_ids'] = lines
                
        return result
    
    _columns = {
        'attendances_ids' : fields.function(_get_attendances, type='many2many', relation='hr.attendance', method=True, string='Attendances', multi="_total"),
#         'total_attendance': fields.function(_get_attendances, method=True, string='Total Attendance', multi="_total"),
    }
            
hr_overtime()
