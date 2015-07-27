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
from openerp.report import report_sxw
from openerp import pooler
from openerp.osv import osv
from openerp.tools.translate import _
import random
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
DATE_FORMAT = "%Y-%m-%d"

from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, float_compare
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

class Parser(report_sxw.rml_parse):
    
    def __init__(self, cr, uid, name, context):
        super(Parser, self).__init__(cr, uid, name, context=context)
        pool = pooler.get_pool(self.cr.dbname)
        self.localcontext.update({
            'get_emp':self.get_emp,
        })
        
        
    def get_emp(self):
        stt = 0
        result = []
        wizard_data = self.localcontext['data']['form']
        self.from_date = wizard_data['from_date'] or '1999-01-01'
        self.to_date = wizard_data['to_date'] or '9999-01-01'
        self.department_id = wizard_data['department_id'] and wizard_data['department_id'][0] or False
        
        sql = '''  SELECT hr.code AS emp_code, hr.name_related ||' '|| COALESCE(hr.last_name,'') AS emp_name, hd.code AS dep_code, 
                           hd.name AS dep_name, hs.from_date, hs.end_date, hst.name AS slog_type
                    FROM hr_employee hr 
                    INNER JOIN hr_slog hs ON hr.id = hs.employee_id
                    LEFT JOIN hr_department hd ON hr.department_id = hd.id
                    LEFT JOIN hr_slog_type hst ON hs.type_id = hst.id
                    WHERE (hs.from_date IS NULL OR hs.from_date >= '%s')
                    AND  (hs.end_date IS NULL OR hs.end_date <= '%s')
                    ''' %(self.from_date,self.to_date)
        if self.department_id:
            sql += 'AND hr.department_id = %s'%(self.department_id)
        self.cr.execute(sql)
        for line in self.cr.dictfetchall():
            stt += 1
            dic = {
                   'stt': stt,
                   'emp_code': line['emp_code'],
                   'emp_name': line['emp_name'] ,
                   'dep_code': line['dep_code'],
                   'dep_name': line['dep_name'],
                   'from_date': line['from_date'],
                   'end_date': line['end_date'],
                   'slog_type': line['slog_type'],
            }
            result.append(dic)
        return result
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

