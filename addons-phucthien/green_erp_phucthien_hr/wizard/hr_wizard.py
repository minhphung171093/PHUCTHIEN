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

class wizard_employee_payslip(osv.osv_memory):
    _name = 'vsis.employee.payslip'
    _columns = {
                'template':fields.many2one('hr.template',"Mẫu"),
                'date_start': fields.date('Từ ngày'),
                'date_stop': fields.date('Đến ngày'),
                'department': fields.many2many('hr.department','att_department_rel_pay', 
                                                 'department_id','att_id','Phòng ban',required = True),                           
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

