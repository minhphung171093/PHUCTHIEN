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
        self.start_date = False,
        self.end_date = False,
        self.department = False
        
        self.localcontext.update({
            'time': time,
            'get_vietname_date':self.get_vietname_date, 
            'get_start_date':self.get_start_date,
            'get_end_date':self.get_end_date,
            'get_gd': self.get_gd,
            'convert':self.convert,
            'birthday': self.birthday,
            'get_department': self.get_department,  
        })
    
    def get_header(self):
        wizard_data = self.localcontext['data']['form']
        
        self.start_date = wizard_data['date_from'] or False
        self.end_date = wizard_data['date_to'] or False
        self.department = wizard_data['department'] or False
        
        return True
    
    def get_start_date(self):
        self.get_header()
        return self.get_vietname_date(self.start_date) 
    
    def get_end_date(self):
        return self.get_vietname_date(self.end_date) 
    
    def get_vietname_date(self, date):
        if not date:
            return ''
        date = datetime.strptime(date, DATE_FORMAT)
        return date.strftime('%d/%m/%Y')
    
    
    def convert(self,amount):
        amt_vn = amount_to_text_vn.amount_to_text_vn(amount,'VND');
        return amt_vn


    def get_department(self):
        result = []
        if not self.department: 
            self.get_header(self)
        if self.department: 
            department = self.pool.get('hr.department').browse(self.cr,self.uid,self.department)
            for d in department:
                sql = ''' select emp.id from hr_employee emp where emp.department_id = %s  ''' %(d.id)
                self.cr.execute(sql)
                ids = map(lambda x: x[0], self.cr.fetchall())
                if len(ids)>=1:
                    count = 0
                    for id in ids:
                        contract_emp_ids = self.pool.get('hr.contract').search(self.cr,self.uid,[('employee_id','=',id)])
                        contract_emp = self.pool.get('hr.contract').browse(self.cr,self.uid,contract_emp_ids)
                        if contract_emp:
                            if self.start_date:
                                if contract_emp[0].trial_date_end <= self.end_date  and contract_emp[0].trial_date_end >= self.start_date:
                                    count +=1
                                    break
                            else:
                                if contract_emp[0].trial_date_end <= self.end_date:
                                    count +=1
                                    break
                    if count >=1:        
                        dic = {
                               'id': d.id or None,
                               'name': d.name or ''
                        }
                        result.append(dic)
        return result
        
    def get_gd(self,department_id):
        ids = self.pool.get('hr.employee').search(self.cr,self.uid,[])
        list_employee = self.pool.get('hr.employee').browse(self.cr,self.uid,ids)
        result =[]
        dic = {}
        stt = 0
        if self.department: 
            department = self.pool.get('hr.department').browse(self.cr,self.uid,self.department)
            for d in department:
                sql = ''' select emp.id from hr_employee emp where emp.department_id = %s  ''' %(d.id)
                self.cr.execute(sql)
                ids = map(lambda x: x[0], self.cr.fetchall())
                list_employee = self.pool.get('hr.employee').browse(self.cr,self.uid,ids)
                for id in list_employee:
                    start_date =''
                    name = id.last_name and id.last_name + ' ' + id.name_related or id.name_related 
                    address = ''
        #            trying_date = id.stop_trying_date
                    address = ''
                    street = id.address_home_id and id.address_home_id.street or ''
                    city = id.address_home_id and id.address_home_id.city or ''
                    state = id.address_home_id and (id.address_home_id.state_id and id.address_home_id.state_id.name or '') or ''
                    if street:
                        address += street
                    if city:
                        address = address + ',' + city 
                    if state:
                        address = address + ',' + state   
                    if id.level_id and id.level_id:      
                        level = self.pool.get('hr.recruitment.degree').read(self.cr,self.uid,[id.level_id.id],['name'])  
                    contract_emp_ids = self.pool.get('hr.contract').search(self.cr,self.uid,[('employee_id','=',id.id)])
                    contract_emp = self.pool.get('hr.contract').browse(self.cr,self.uid,contract_emp_ids)
                    stop_working_date = id.stop_working_date
                    date_end = time.strftime('%Y-%m-%d')
                    if not stop_working_date or  stop_working_date> date_end:
                        if contract_emp:
                            if self.start_date:
                                if contract_emp[0].trial_date_end >= self.start_date and contract_emp[0].trial_date_end <=self.end_date:
                                    if id.department_id.id == department_id:
                                        stt += 1      
                                        dic = {
                                                'id': id.id,
                                                'stt': stt,
                                                'code': id.emp_code,
                                                'name':name,
                    #                            'trying_date':trying_date,
                                                'birthday': id.birthday,
                                                'department': id.department_id and id.department_id.name or '',
                                                'job':id.job_id and id.job_id.name or '',
                                                'address': address,
                                                'religion':id.religion_id and id.religion_id.name or '',
                                                'start_date': start_date,
                                                #'level': len(level)>0 and level[0]['name'] or '',
                                                'id_cm': id.identification_id  or '',
                                                'id_place': id.identification_id_place and id.identification_id_place.name or '',
                                                'id_date': id.identification_id_date and time.strftime('%d/%m/%Y', time.strptime(id.identification_id_date, '%Y-%m-%d')) or '',
                                                'trial_date_end': contract_emp[0].trial_date_end and time.strftime('%d/%m/%Y', time.strptime(contract_emp[0].trial_date_end, '%Y-%m-%d')) or '',
                                               }
                                        result.append(dic)
                            else:
                                if contract_emp[0].trial_date_end <=self.end_date:
                                    if id.department_id.id == department_id:
                                        stt += 1      
                                        dic = {
                                                'id': id.id,
                                                'stt': stt,
                                                'code': id.emp_code,
                                                'name':name,
                    #                            'trying_date':trying_date,
                                                'birthday': id.birthday,
                                                'department': id.department_id and id.department_id.name or '',
                                                'job':id.job_id and id.job_id.name or '',
                                                'address': address,
                                                'religion':id.religion_id and id.religion_id.name or '',
                                                'start_date': start_date,
                                                #'level': len(level)>0 and level[0]['name'] or '',
                                                'id_cm': id.identification_id  or '',
                                                'id_place': id.identification_id_place and id.identification_id_place.name or '',
                                                'id_date': id.identification_id_date and time.strftime('%d/%m/%Y', time.strptime(id.identification_id_date, '%Y-%m-%d')) or '',
                                                'trial_date_end': contract_emp[0].trial_date_end and time.strftime('%d/%m/%Y', time.strptime(contract_emp[0].trial_date_end, '%Y-%m-%d')) or '',
                                               }
                                        result.append(dic)
                                
                                
#                                    print 'nhung dieu nho nhat lam ta chan',result
        return result
        
    def birthday(self,emp,male):
        birthday  = ''
        employee = self.pool.get('hr.employee').read(self.cr,self.uid,emp,['gender','birthday'])
        if male == employee['gender']:
            birthday = employee['birthday'] and time.strftime('%d/%m/%Y', time.strptime(employee['birthday'], '%Y-%m-%d'))or '', 
        return birthday 
        

    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
