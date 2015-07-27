
import datetime
from datetime import date
import time
from itertools import groupby
from operator import itemgetter

import math
from openerp import netsvc
from openerp import tools
from openerp.osv import fields, osv
from openerp.tools.translate import _

class hr_holidays(osv.osv):
    _inherit = "hr.holidays"
    
    def _day_compute(self, cr, uid, ids, fieldnames, args, context=None):
        user_pool = self.pool.get('res.users')
        res = dict.fromkeys(ids, '')
        for obj in self.browse(cr, uid, ids, context=context):
            if obj['date_from']:
                date_from_with_timezone = user_pool._convert_user_datetime(cr, uid, obj['date_from'])
                res[obj.id] = date_from_with_timezone.strftime('%Y-%m-%d')
        return res
    
    _columns = {
        'day': fields.function(_day_compute, type='date', string='Day', select=1, 
                                           store={
                                'hr.holidays': (lambda self, cr, uid, ids, c={}: ids, ['date_from'], 10),
                            }),
    }
    
    def default_get(self, cr, uid, fields, context=None):
        res = super(hr_holidays, self).default_get(cr, uid, fields, context=context)
        if context.get('active_id',False):
            res.update({'employee_id':context['active_id']})
        status_ids = self.pool.get('hr.holidays.status').search(cr, uid, [('limit','=',False)])
        res.update({'holiday_status_id':status_ids and status_ids[0] or False})
        return res
    
hr_holidays()

class hr_holidays_status(osv.osv):
    _inherit = "hr.holidays.status"
    _columns = {                   
                'paid_method' : fields.selection([('paid','Paid'),('un-paid','Un-paid')],'Paid/Un-Paid',required=True),
                'auto_create' :fields.boolean('Auto Create'),
                'number_days': fields.float('Number Days'),
            }
    
    def generate_allocation_request(self, cr, uid, ids, context=None):
        hr_holidays_pool = self.pool.get('hr.holidays')
        hr_employee_pool = self.pool.get('hr.employee')
        wf_service = netsvc.LocalService("workflow")
        now = time.strftime("%Y-%m-%d")
        for status in self.browse(cr, uid, ids):
            if status.auto_create:
                if status.number_days > 0:
                    cr.execute('''
                        SELECT employee_id 
                        FROM hr_contract 
                        WHERE (date_end is null or date_end > '%s') and 
                        employee_id not in (SELECT employee_id FROM hr_holidays WHERE holiday_status_id = %s AND type = 'add')
                    '''%(now, status.id))
                    employee_ids = [x[0] for x in cr.fetchall()]
                    for employee in hr_employee_pool.browse(cr, uid, employee_ids):
                        vals = {
                            'name': '[' + status.name + '] - ' + employee.name,
                            'holiday_status_id': status.id,
                            'employee_id': employee.id, 
                            'type':'add',
                            'number_of_days_temp': status.number_days,
                        }
                        new_id = hr_holidays_pool.create(cr, uid, vals)
                        wf_service.trg_validate(uid, 'hr.holidays', new_id, 'confirm', cr)
                        wf_service.trg_validate(uid, 'hr.holidays', new_id, 'validate', cr)
                        wf_service.trg_validate(uid, 'hr.holidays', new_id, 'second_validate', cr) 
        return True
    
hr_holidays_status()
    