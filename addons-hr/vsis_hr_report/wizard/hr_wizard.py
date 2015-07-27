#import wizard
import netsvc
import time
import pooler
from tools import config
from osv import osv, fields
#from mx import DateTime
from datetime import date, datetime, timedelta
from tools.translate import _    

from datetime import date
from datetime import datetime
from datetime import timedelta
from dateutil import relativedelta

def _default_month(self, cr, uid, ids, context={}): 
        month = time.strftime('%m', time.strptime(time.strftime('%Y-%m-%d'), '%Y-%m-%d'))
        return str(int(month))

def _default_year(self, cr, uid, ids, context={}): 
        year = time.strftime('%Y', time.strptime(time.strftime('%Y-%m-%d'), '%Y-%m-%d'))
        return int(year)

class wizard_list_employee_tv(osv.osv_memory):
    _name = 'list.employee.tv'
    _columns = {
                
                'date_from': fields.date('Date_from'),
                'date_to': fields.date('Date_to', required=True),
                'department': fields.many2many('hr.department','att_department_rel_tv', 
                                                 'department_id','att_id','Deparment',required = True), 
    }
    _defaults = {
        'date_to': lambda *a: time.strftime('%Y-%m-%d'),
    }
      
    def print_report(self, cr, uid, ids, context=None):
        datas = {'ids': context.get('active_ids', [])}
        datas['model'] = 'list.employee.tv'
        datas['form'] = self.read(cr, uid, ids)[0]
        return {'type': 'ir.actions.report.xml', 'report_name': 'list_employee_tv' , 'datas': datas
        }  
    
wizard_list_employee_tv()

class wizard_vsis_giam_ld(osv.osv_memory):
    _name = 'vsis.giam.ld'
    _columns = {
               'date_start': fields.date('Start Date'),
               'date_stop': fields.date('End Date'),
    }
    _defaults = {
        'date_start': lambda *a: time.strftime('%Y-%m-01'),
        'date_stop' : lambda *a: str(datetime.now() + relativedelta.relativedelta(months=+1, day=1, days=-1))[:10],
    }  
      
    def print_report(self, cr, uid, ids, context=None):
        datas = {'ids': context.get('active_ids', [])}
        datas['model'] = 'vsis.giam.ld'
        datas['form'] = self.read(cr, uid, ids)[0]
        return {'type': 'ir.actions.report.xml', 'report_name': 'giam_ld' , 'datas': datas
        }  
     
wizard_vsis_giam_ld()

class wizard_vsis_su_dung_ld(osv.osv_memory):
    _name = 'vsis.su.dung.ld'
    _columns = {
               'date_start': fields.date('Start Date'),
               'date_stop': fields.date('End Date'),
    }
    _defaults = {
        'date_start': lambda *a: time.strftime('%Y-%m-01'),
        'date_stop' : lambda *a: str(datetime.now() + relativedelta.relativedelta(months=+1, day=1, days=-1))[:10],
    }  
      
    def print_report(self, cr, uid, ids, context=None):
        datas = {'ids': context.get('active_ids', [])}
        datas['model'] = 'vsis.su.dung.ld'
        datas['form'] = self.read(cr, uid, ids)[0]
        return {'type': 'ir.actions.report.xml', 'report_name': 'su_dung_ld' , 'datas': datas
        }  

wizard_vsis_su_dung_ld()  

class wizard_employee_payslip(osv.osv_memory):
    _name = 'vsis.employee.payslip'
    _columns = {
#                'option': fields.selection([('per','period'),('date','Date')], 'State', required=True),
#                'period': fields.many2one('gs.hr.period',"Period"),
                'template':fields.many2one('hr.template',"Template"),
                'date_start': fields.date('Start Date'),
                'date_stop': fields.date('End Date'),
#                'period_end': fields.many2one('gs.hr.period',"End Period"),  
                'department': fields.many2many('hr.department','att_department_rel_pay', 
                                                 'department_id','att_id','Deparment',required = True),                           
    }
    
    _defaults = {
        'date_start': lambda *a: time.strftime('%Y-%m-01'),
        'date_stop' : lambda *a: str(datetime.now() + relativedelta.relativedelta(months=+1, day=1, days=-1))[:10],
    }  
      
    def print_report(self, cr, uid, ids, context=None):
        datas = {'ids': context.get('active_ids', [])}
        datas['model'] = 'vsis.employee.payslip'
        datas['form'] = self.read(cr, uid, ids)[0]
        return {'type': 'ir.actions.report.xml', 'report_name': 'employee_payslip' , 'datas': datas
        }  
         
    def check(self,cr,uid,ids,date_stop,date_start):
        if date_stop < date_start:
            raise osv.except_osv(_('Error !'), _('Date End must than Date From.'))
        else:
            return {'value': {'date_stop': date_stop}}
        
wizard_employee_payslip()

