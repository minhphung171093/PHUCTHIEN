# -*- coding: utf-8 -*-
##############################################################################
#
#    HLVSolution, Open Source Management Solution
#
##############################################################################

import time
from report import report_sxw
import pooler
from osv import osv
from tools.translate import _
import random
from datetime import datetime
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
DATE_FORMAT = "%Y-%m-%d"

class Parser(report_sxw.rml_parse):
        
    def __init__(self, cr, uid, name, context):
        super(Parser, self).__init__(cr, uid, name, context=context)
        pool = pooler.get_pool(self.cr.dbname)
        self.vat = False
        self.localcontext.update({
            'get_nv':self.get_nv,
        })
        
    def convert(self,amount):
        amt_vn = amount_to_text_vn.amount_to_text_vn(amount,'VND');
        return amt_vn
    

    
    def number_month(self,date_start,date_end):
        date_s = date_start[8:10]
        month_s = date_start[5:7]
        year_s = date_start[0:4]
           
        date_e = date_end[8:10]
        month_e = date_end[5:7] 
        year_e = date_end[0:4]
        n =  datetime.datetime(int(year_e),int(month_e),int(date_e))- datetime.datetime(int(year_s),int(month_s),int(date_s))  
        n = n.days
        month = divmod(n,30) 
        return month[0]

    def get_nv(self,id):
        e_con = self.pool.get('hr.contract').browse(self.cr, self.uid,id)
        id_e = e_con.employee_id and e_con.employee_id.id or ''
        employee = self.pool.get('hr.employee').browse(self.cr,self.uid,id_e) 
#        employee_account = employee.employee_account and employee.employee_account.name or ''
        start_date = ''
        place_of_birth = e_con.employee_id and (e_con.employee_id.place_of_birth and e_con.employee_id.place_of_birth.name  or '') or ''    
        cmnd = e_con.employee_id and e_con.employee_id.identification_id or ''
        nc = e_con.employee_id and (e_con.employee_id.identification_id_place and e_con.employee_id.identification_id_place.name or '') or ''
        date_id = e_con.employee_id and e_con.employee_id.identification_id_date or ''
        ssnid = e_con.employee_id and e_con.employee_id.sinid or '',
        ssnid_place = e_con.employee_id and (e_con.employee_id.sinid_place and e_con.employee_id.sinid_place.name or '') or ''
        ssnid_date = e_con.employee_id and e_con.employee_id.sinid_date  or ''
        start_date_contract = e_con.date_start
        end_date_contract = e_con.date_end
        trial_date_start = e_con.trial_date_start
        trial_date_end = e_con.trial_date_end
        ratio = e_con.grade_id and e_con.grade_id.ratio or '',
#        print  'dddddddddddddddd',ratio
#        month = 0
#        if start_date_contract:
#            year_start = int(time.strftime('%Y', time.strptime(start_date_contract, '%Y-%m-%d')))
#            month_start = int(time.strftime('%m', time.strptime(start_date_contract, '%Y-%m-%d')))
#            date_start = int(time.strftime('%d', time.strptime(start_date_contract, '%Y-%m-%d')))
#       
#        if end_date_contract:    
#            year_end = int(time.strftime('%Y', time.strptime(end_date_contract, '%Y-%m-%d')))
#            month_end = int(time.strftime('%m', time.strptime(end_date_contract, '%Y-%m-%d')))
#            date_end = int(time.strftime('%d', time.strptime(end_date_contract, '%Y-%m-%d')))
#        else:
#            end_date_contract = start_date_contract
#            year_end = int(time.strftime('%Y', time.strptime(end_date_contract, '%Y-%m-%d')))
#            month_end = int(time.strftime('%m', time.strptime(end_date_contract, '%Y-%m-%d')))
#            date_end = int(time.strftime('%d', time.strptime(end_date_contract, '%Y-%m-%d')))
#               
#        month = self.number_month(start_date_contract, end_date_contract)        
#        work_location = e_con.work_location.name
        name = employee.name
        last = employee.last_name
        last_name = ''
        if last:
            last_name += last + ' '
        if name:
            last_name += name
          
        street = employee.address_home_id and employee.address_home_id.street or ''
        city = employee.address_home_id and employee.address_home_id.city or ''
        state = employee.address_home_id and (employee.address_home_id.state_id and employee.address_home_id.state_id.name or '') or ''
        address = ''
        if street:
            address += street + ', ' 
        if city:
            address += city + ', '
        if state:
            address += state 
            
        street = employee.address_temp_id.street
        city = employee.address_temp_id.city
        state = employee.address_temp_id and (employee.address_temp_id.state_id and employee.address_temp_id.state_id.name or '') or ''
        address_temp = ''
        if street:
            address_temp += street + ', ' 
        if city: 
            address_temp +=  city + ', '
        if state:
            address_temp += state  
        major =''
        str_name_m = ''
        for m in employee.major_ids:
            str_name_m = m.name
            if major:
                major = major + ', ' + str_name_m
            else:
                major = str_name_m    
        dic = {
                'last_name': last_name,
                'country': employee.country_id.name,
                'birthday': employee.birthday and time.strftime('%d/%m/%Y', time.strptime(employee.birthday, '%Y-%m-%d')),
                'birthday_date':employee.birthday and time.strftime('%d', time.strptime(employee.birthday, '%Y-%m-%d')),
                'birthday_month':employee.birthday and time.strftime('%m', time.strptime(employee.birthday, '%Y-%m-%d')),
                'birthday_year':employee.birthday and time.strftime('%Y', time.strptime(employee.birthday, '%Y-%m-%d')),
                'job': employee.job_id.name,
                'address_home': address,
                'address_temp': address_temp,
                'place_of_birth': place_of_birth,
                'ssnid': ssnid,
                'ssnid_date': ssnid_date,
                'ssnid_place': ssnid_place,
                'ssnid_date_date':ssnid_date and time.strftime('%d', time.strptime(ssnid_date, '%Y-%m-%d')),
                'ssnid_date_month': ssnid_date and time.strftime('%m', time.strptime(ssnid_date, '%Y-%m-%d')),
                'ssnid_date_year': ssnid_date and time.strftime('%Y', time.strptime(ssnid_date, '%Y-%m-%d')),
                'cmnd': cmnd,
                'start_date':start_date and time.strftime('%d/%m/%Y', time.strptime(start_date, '%Y-%m-%d')),
                'nc': nc,
                'date_id':date_id and time.strftime('%d/%m/%Y', time.strptime(date_id, '%Y-%m-%d')),
                'date_id_date':date_id and time.strftime('%d', time.strptime(date_id, '%Y-%m-%d')),
                'date_id_month': date_id and time.strftime('%m', time.strptime(date_id, '%Y-%m-%d')), 
                'date_id_year': date_id and time.strftime('%Y', time.strptime(date_id, '%Y-%m-%d')), 
#                'time_contract': month or 0,
#                'date_start': date_start,
#                'month_start': month_start,
#                'year_start':year_start, 
#                'date_end': date_end,
#                'month_end': month_end,
#                'year_end':year_end, 
                'start_date_contract':start_date_contract and time.strftime('%d/%m/%Y', time.strptime(start_date_contract, '%Y-%m-%d')) or '',
                'start_date_contract_date':start_date_contract and time.strftime('%d', time.strptime(start_date_contract, '%Y-%m-%d')) or '',
                'start_date_contract_month':start_date_contract and time.strftime('%m', time.strptime(start_date_contract, '%Y-%m-%d')) or '',
                'start_date_contract_year':start_date_contract and time.strftime('%Y', time.strptime(start_date_contract, '%Y-%m-%d')) or '',
                'end_date_contract' : end_date_contract and time.strftime('%d/%m/%Y', time.strptime(end_date_contract, '%Y-%m-%d')) or '',
                'end_date_contract_date' : end_date_contract and time.strftime('%d', time.strptime(end_date_contract, '%Y-%m-%d')) or '',
                'end_date_contract_month' : end_date_contract and time.strftime('%m', time.strptime(end_date_contract, '%Y-%m-%d')) or '',
                'end_date_contract_year' : end_date_contract and time.strftime('%Y', time.strptime(end_date_contract, '%Y-%m-%d')) or '',
                'trial_date_start':trial_date_start and time.strftime('%d/%m/%Y', time.strptime(trial_date_start, '%Y-%m-%d')) or '',
                'trial_date_start_date':trial_date_start and time.strftime('%d', time.strptime(trial_date_start, '%Y-%m-%d')) or '',
                'trial_date_start_month':trial_date_start and time.strftime('%m', time.strptime(trial_date_start, '%Y-%m-%d')) or '',
                'trial_date_start_year':trial_date_start and time.strftime('%Y', time.strptime(trial_date_start, '%Y-%m-%d')) or '',
                'trial_date_end':trial_date_start and time.strftime('%d/%m/%Y', time.strptime(trial_date_start, '%Y-%m-%d')) or '',
                'trial_date_end_date':trial_date_start and time.strftime('%d', time.strptime(trial_date_start, '%Y-%m-%d')) or '',
                'trial_date_end_month':trial_date_start and time.strftime('%m', time.strptime(trial_date_start, '%Y-%m-%d')) or '',
                'trial_date_end_year':trial_date_start and time.strftime('%Y', time.strptime(trial_date_start, '%Y-%m-%d')) or '',
                'name':e_con.name,
                'ratio': ratio,
                'total_wage': e_con.total_wage or 0,
                'wage': e_con.wage or 0,
                'duration': e_con.duration_type and e_con.duration_type.name or '',
                'gender': employee.gender,
                'major': major
               }
        return dic
    
    def gender(self,o,gt):
        gender = o.employee_id and o.employee_id.gender or ''
        if gender == gt:
            return 'X' 
        else:
            return ''
        
        
    def conver_strdate_to_date_or_datetime(self,strdate,result):
        if result=="date":
            dt_date=datetime.date(int(strdate[0:4]),int(strdate[5:7]),int(strdate[8:10]))
        else:
            dt_date=datetime.datetime(int(strdate[0:4]),int(strdate[5:7]),int(strdate[8:10]))
        return dt_date
    
    def get_date_now(self):
        from datetime import datetime
        date_current = str(datetime.now())
        date_cur = self.conver_strdate_to_date_or_datetime(date_current, 'date')
        date_cur = str(date_cur)
        date = time.strftime('%d', time.strptime(date_cur, '%Y-%m-%d'))
        month = time.strftime('%m', time.strptime(date_cur, '%Y-%m-%d'))
        year = time.strftime('%Y', time.strptime(date_cur, '%Y-%m-%d'))
        return {'date':date,'month':month,'year':year} 
    
    
    def _address(self, partner, separator=', ', country=True, state=True, city=True, street=True):
        if partner:
            if street:
                dc = partner.street or ''
                if city and partner.city:
                    dc += separator + partner.city
                if state and partner.state_id:
                    dc += separator + partner.state_id.name
                if country and partner.country_id:
                    dc += separator + partner.country_id.name
            else:
                dc = partner.street2 or ''
            res = {
                'dc': dc,
                'fax': partner.fax or '',
                'phone': partner.mobile or '',
                'email': partner.email or '',
                'name': partner.name or ''
            }
        else:
            res = {
               'dc': '',
               'fax': '',
               'phone': '',
               'email': '',
               'name': '',
        }
            
        return res
    
    def get_work_addr(self,obj):
        if not obj:
            return {}
        else:
            emp_id = obj.employee_id and obj.employee_id.id
            emp = emp_id and self.pool.get('hr.employee').browse(self.cr,self.uid,emp_id)
            addr = emp and emp.address_id
        return emp.address_id   

    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
