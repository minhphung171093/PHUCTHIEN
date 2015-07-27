
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
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, DATETIME_FORMATS_MAP, float_compare

class hr_holiday_day(osv.osv):
    _name = "hr.holiday.day"
    _order = "date_from desc"
    
    def _check_date(self, cr, uid, ids):
        for day in self.browse(cr, uid, ids):
            day_ids = self.search(cr, uid, [('date_from', '<=', day.date_to), ('date_to', '>=', day.date_from), ('id', '<>', day.id)])
            if day_ids:
                return False
        return True
    
    _columns = {
                    'name': fields.char('Name', size=250, select=1, required=True),
                    'date_from': fields.date('Date From', select=1, required=True),
                    'date_to': fields.date('Date To', select=1, required=True),
                }
    
    _defaults = {
        'date_from': time.strftime(DEFAULT_SERVER_DATE_FORMAT),
        'date_to': time.strftime(DEFAULT_SERVER_DATE_FORMAT),
    }
    
    _constraints = [
        (_check_date, 'You can not have 2 leaves that overlaps on same day!', ['date_from','date_to']),
    ]
    
    _sql_constraints = [
        ('date_check', "CHECK (date_from <= date_to)", "The start date must be anterior to the end date."),
    ]
    
    def onchange_date_from(self, cr, uid, ids, date_from, date_to):
        # date_to has to be greater than date_from
        if (date_from and date_to) and (date_from > date_to):
            raise osv.except_osv(_('Warning!'),_('The start date must be anterior to the end date.'))

        result = {'value': {'date_to':date_from}}
        return result

    def onchange_date_to(self, cr, uid, ids, date_from, date_to):
        # date_to has to be greater than date_from
        if (date_from and date_to) and (date_from > date_to):
            raise osv.except_osv(_('Warning!'),_('The start date must be anterior to the end date.'))

        result = {'value': {}}

        return result
    
hr_holiday_day()    