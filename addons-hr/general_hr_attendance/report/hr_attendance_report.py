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
from report import report_sxw
import pooler
from osv import osv
from tools.translate import _
import random
from datetime import datetime
from dateutil.relativedelta import relativedelta
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
DATE_FORMAT = "%Y-%m-%d"

class Parser(report_sxw.rml_parse):
        
    def __init__(self, cr, uid, name, context):
        super(Parser, self).__init__(cr, uid, name, context=context)
        self.user_obj = pooler.get_pool(self.cr.dbname).get('res.users')
        self.cr = cr
        self.uid = uid
        self.emp_ids = False
        self.month = False
        self.year = False
        self.localcontext.update({
            'get_emp': self.get_emp,
            'get_timesheet': self.get_timesheet,
            'get_total_timesheet': self.get_total_timesheet,
            'get_month': self.get_month,
            'get_year': self.get_year,
        })
        
    def get_header(self):
        wizard_data = self.localcontext['data']['form']
        self.emp_ids = wizard_data['employee_ids'] or False
        self.month = wizard_data['month'] or False
        self.year = wizard_data['year'] or False
        
    def get_emp(self):
        stt = 0
        if not self.emp_ids:
            self.get_header();
        result = []
        list_emp = str(self.emp_ids).replace("[","(")
        list_emp = list_emp.replace("]",")")
        sql = ''' 
                select hr.id, hr.name_related as first_name, hr.last_name,hj.name as job_name
                from hr_employee hr
                left join hr_job hj on hr.job_id = hj.id
                where hr.id in %s
              '''%(list_emp)
        self.cr.execute(sql)
        for line in self.cr.dictfetchall():
            stt += 1
            dic = {
                   'stt': stt,
                   'employee_id': line['id'],
                   'first_name': line['first_name'] or False,
                   'last_name': line['last_name'] or False,
                   'job_name':line['job_name'] or False
            }
            result.append(dic)
        return result
    def get_timesheet(self,emp_id,day):
        if not self.month:
            self.get_header();
        time_normal = 0
        sql = ''' 
                select round(time_normal::numeric,2) as time
                from hr_attendance_timesheet
                where employee_id = %s 
                and extract(DAY FROM date) = %s
                and extract(MONTH FROM date) = %s
                and extract(YEAR FROM date) = %s
              '''%(emp_id,day,self.month,self.year)
        self.cr.execute(sql)
        line = self.cr.dictfetchall()
        if line and line[0]:
            time_normal = line[0]['time'] or 0.0
        return time_normal
    
    def get_total_timesheet(self,emp_id):
        if not self.month:
            self.get_header();
        time_normal = 0
        sql = ''' 
                select round(sum(time_normal/8)::numeric,2) as time
                from hr_attendance_timesheet
                where employee_id = %s 
                and extract(MONTH FROM date) = %s
                and extract(YEAR FROM date) = %s
              '''%(emp_id,self.month,self.year)
        self.cr.execute(sql)
        line = self.cr.dictfetchall()
        if line and line[0]:
            time_normal = line[0]['time'] or 0.0
        return time_normal
    
    def get_month(self):
        if not self.month:
            self.get_header();
        return self.month
    def get_year(self):
        if not self.year:
            self.get_header();
        return self.year
