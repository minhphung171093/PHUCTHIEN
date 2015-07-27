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

class wizard_gs_purvey_insurance(osv.osv_memory):
    _name = 'gs.purvey.insurance'
    _columns = {
               'date_start': fields.date('Start Date'),
               'date_stop': fields.date('End Date'),
    }
    _defaults = {
        'date_start': lambda *a: time.strftime('%Y-%m-01'),
        'date_stop' : lambda *a: str(datetime.now() + relativedelta.relativedelta(months=+1, day=1, days=-1))[:10],
    }  
      
    def print_report(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        datas = {'ids': context.get('active_ids', [])}

        res = self.read(cr, uid, ids, ['date_start','date_stop'], context=context)
        res = res and res[0] or {}
        datas['form'] = res
        datas['model']= 'hr.employee'
        return {
        'type': 'ir.actions.report.xml',
        'report_name': 'gs_purvey_insurance',
        'datas': datas,
        }  
     
wizard_gs_purvey_insurance()

