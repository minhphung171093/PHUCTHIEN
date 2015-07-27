
import time
from datetime import datetime,timedelta
from dateutil.relativedelta import relativedelta
from itertools import groupby
from operator import itemgetter
from decimal import *  
import math
from openerp import netsvc
from openerp import tools
from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, DATETIME_FORMATS_MAP, float_compare
import openerp.addons.decimal_precision as dp

class hr_employee(osv.osv):
    _inherit = "hr.employee"
    
    def cal_year(self,cr, uid,date_from,date_to, context=None):
        
        count_year = 0
        while date_to > date_from :
            date_from =  date_from + relativedelta(years = 1)
            count_year += 1
        return (count_year - 1)
        
    def cal_month(self,cr, uid,date_from,date_to,context=None):
        
        res={}
        count_month = 0
        while date_to >= date_from:
            date_from = date_from + relativedelta(months = 1)
            count_month += 1
        return count_month - 1
        
    def cal_round_month_by_year(self,cr, uid,date_from,date_to,context=None):
        
        res={}
        nub_of_years = self.cal_year(cr, uid,date_from,date_to)
        new_round_date = date_from + relativedelta(years = nub_of_years)
        nub_of_months = self.cal_month(cr, uid,new_round_date,date_to)
        return nub_of_months
    
    def _cal_worked_years(self, cr, uid, ids, field_name, arg, context=None):
         
         res = {}
         for employee in self.browse(cr, uid, ids, context=context):
            res[employee.id] = 0
            if employee.joining_date:
                  now = datetime.utcnow()
                  joining_date = datetime.strptime(employee.joining_date,DEFAULT_SERVER_DATE_FORMAT)
                  nub_of_years = self.cal_year(cr, uid,joining_date,now)
                  if self.cal_round_month_by_year(cr, uid,joining_date,now) >= 1:
                      nub_of_years += 1
                  res[employee.id] = nub_of_years      
         return res
    
    _columns = {
        'joining_date': fields.date('Joining Date', required=True),
#         'worked_years': fields.function(_cal_worked_years, type="integer", string='Worked Years', readonly=True,
#             store={
#                 'hr.employee': (lambda self, cr, uid, ids, c={}: ids, ['joining_date'], 10),
#             }),
        'worked_years': fields.float('Worked Years', digits=(16,2)),
        'employee_history': fields.one2many('hr.employee.history','employee_id', 'History', readonly=True),
        'dependant_of_taxpayer': fields.integer('Dependant'),
    }
    
    def write(self, cr, uid, ids, vals, context=None):
        employee_history_pool = self.pool.get('hr.employee.history')
        for line in self.browse(cr, uid, ids):
            employee_history_vals = {}
            if vals.get('parent_id',False):
                employee_history_vals.update({'parent_id':line.parent_id.id or False})
            if vals.get('department_id',False):
                employee_history_vals.update({'department_id':line.department_id.id or False})
            if vals.get('job_id',False):
                employee_history_vals.update({'job_id':line.job_id.id  or False})
            
            if vals.get('joining_date',False):
                employee_history_vals.update({'joining_date':line.joining_date or False})
            if vals.get('worked_years',False):
                employee_history_vals.update({'worked_years':line.worked_years or False})
            
            if employee_history_vals:
                employee_history_vals.update({'employee_id':line.id})
                employee_history_pool.create(cr, uid, employee_history_vals)
        return super(hr_employee, self).write(cr, uid, ids, vals, context)
    
   
hr_employee()

class hr_employee_history(osv.osv):
    _name = 'hr.employee.history'
    _order = 'create_date desc'
    _columns = {
        'create_date': fields.datetime('Create Date', readonly=True),
        'user_id': fields.many2one('res.users','User', readonly=True),
        'parent_id': fields.many2one('hr.employee', 'Manager'),
        'department_id':fields.many2one('hr.department', 'Department', readonly=True),
        'job_id': fields.many2one('hr.job', 'Job', readonly=True),
        'joining_date': fields.date('Joining Date', readonly=True),
        'worked_years': fields.float('Worked Years', digits=(16,2)),
        'employee_id': fields.many2one('hr.employee', 'Employee', required=True, ondelete='cascade', select=True),
    }
    
    _defaults = {
        'user_id': lambda obj,cr,uid,context=None: uid,
    }
    
hr_employee_history()