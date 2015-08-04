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
import func_bodau


DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
DATE_FORMAT = "%Y-%m-%d"

class Parser(report_sxw.rml_parse):
        
    def __init__(self, cr, uid, name, context):
        super(Parser, self).__init__(cr, uid, name, context=context)
        pool = pooler.get_pool(self.cr.dbname)
        self.company_name = False
        self.template = False
        self.start_date =  False
        self.end_date =  False
        self.get_company(cr, uid)
        
        self.stt = 0
        self.rule = []
        self.department = False
        self.localcontext.update({
            
            'get_company_name':self.get_company_name,
            'get_company_address':self.get_company_address,       
            'get_start_date':self.get_start_date,
            'get_end_date':self.get_end_date,      
            'time': time,
            'get_data': self.get_data,
            'get_rule': self.get_rule,
            'get_department': self.get_department,
            'get_emp': self.get_emp,
            'get_amount': self.get_amount,
            'get_rule_temp': self.get_rule_temp,
            'get_total_dep': self.get_total_dep,
            'get_total_all_dep': self.get_total_all_dep,
            'get_date_work': self.get_date_work,
            'get_date_annual': self.get_date_annual,
            'get_date_business': self.get_date_business,
            'get_total_work': self.get_total_work,
            'get_total_annual': self.get_total_annual,
            'get_total_business': self.get_total_business,
        })
        
    def get_header(self):
        wizard_data = self.localcontext['data']['form']
        self.start_date = wizard_data['date_start'] or False
        self.end_date = wizard_data['date_stop'] or False
        self.template = wizard_data['template'] or False
        self.department = wizard_data['department'] or False
        
    def get_start_date(self):
        self.get_header()
        return self.get_vietname_date(self.start_date) 
    
    def get_end_date(self):
        self.get_header()
        return self.get_vietname_date(self.end_date) 
    
    def get_vietname_date(self, date):
        if not date:
            date = time.strftime(DATE_FORMAT)
        date = datetime.strptime(date, DATE_FORMAT)
        return date.strftime('%d/%m/%Y')
    
    def get_company(self,cr,uid):
         user_obj = self.pool.get('res.users').browse(cr,uid,uid)
         self.company_name = user_obj and user_obj.company_id and user_obj.company_id.name or ''
         self.company_address = user_obj and user_obj.company_id and user_obj.company_id.street or ''
         self.vat = user_obj and user_obj.company_id and user_obj.company_id.vat or ''
         
    def get_company_name(self):
        self.get_header()
        return self.company_name
    
    def get_company_address(self):
        return self.company_address
    
    def get_data(self,data):
        if data and len(data['department'])<=1:
            data['department'].append(-1)
        sql1 = '''  select distinct(rule.id),rule.name,rule.sequence 
        from hr_salary_rule rule order by rule.sequence asc'''
        self.cr.execute(sql1)
        rule = {-1: 'Stt',0: u'Họ và tên'}
        line_rule = {}
        for line in self.cr.dictfetchall():
            rule.update({line['id']: line['name']})
            line_rule.update({line['id'] : 0.0})
#        rule.update({500:u'Tổng'})
#        line_rule.update({500:0.0})
        res = [sorted(rule.iteritems(), key=operator.itemgetter(0))]   
        sql2 = '''  select emp.id as employee_id, emp.name_related as emp_name,
        dep.id as department_id,dep.name as department_name  
        from hr_payslip sl
        left join hr_employee emp on emp.id = sl.employee_id
        left join hr_department dep on dep.id = emp.department_id
        where sl.date_from >= '%s' 
            and sl.date_from <= '%s'
            and sl.date_to >='%s'
            and sl.date_to <='%s'
            and dep.id in %s
        order by dep.name 
  '''%(data['date_start'],data['date_stop'],data['date_start'],data['date_stop'],tuple(data['department']))
        self.cr.execute(sql2)
        stt = 0
        flag_department = False
        data_sum_rule = {}
        total_data_sum_rule = {-1:u'Tổng Cộng', 0 : ''}
        total_data_sum_rule.update(line_rule)
        data_emp = self.cr.dictfetchall()
        for line in data_emp:
            stt +=1
#            key_stt = 5000 - stt
            if flag_department and flag_department != line['department_id']:
                self.stt = 0
                res.append(sorted(data_sum_rule.iteritems(), key=operator.itemgetter(0)))
                flag_department = line['department_id']
                data_sum_rule = {-1:u'Tổng' ,0:  '(' + line['department_name'] +')' }
                data_sum_rule.update(line_rule)
#                print 'tinh tan',data_sum_rule
            if not flag_department:
                flag_department = line['department_id']
                data_sum_rule = {-1:u'Tổng' ,0:  '(' + line['department_name'] +')'}
                data_sum_rule.update(line_rule)
            self.stt += 1
            name =line['emp_name'] or ''
            data_line = {-1 :int(self.stt) ,0:name}
            data_line.update(line_rule)
            sql3 = '''  select emp.id as emp_id ,rule.id as rule_id ,dep.id as depart_id ,line.amount as amount  
            from hr_payslip sl
            left join hr_payslip_line line on sl.id = line.slip_id
            left join hr_salary_rule rule on rule.id = line.salary_rule_id
            left join hr_employee emp on emp.id = sl.employee_id
            left join hr_department dep on dep.id = emp.department_id
            where sl.date_from >= '%s' 
            and sl.date_from <= '%s'
            and sl.date_to >='%s'
            and sl.date_to <='%s'
            and dep.id = %s and emp.id = %s
            GROUP BY dep.id,emp.id,rule.id,line.amount
      '''%(data['date_start'],data['date_stop'],data['date_start'],data['date_stop'],line['department_id'],line['employee_id'])
#            print 'sql 3',sql3
            self.cr.execute(sql3)
#            print 'cr dicfetchall ra nay', self.cr.dictfetchall()     
            for l in self.cr.dictfetchall():
                if l['amount']:
                    data_line[l['rule_id']] += l['amount'] or 0
#                    data_line[500] += l['amount'] or 0
                    data_sum_rule[l['rule_id']] += l['amount'] or 0
#                    data_sum_rule[500] += l['amount']
                    total_data_sum_rule[l['rule_id']] += l['amount']  
#            print 'data line o phia duoi',data_line        
            res.append(sorted(data_line.iteritems(), key=operator.itemgetter(0)))
#            print 'tieu ru',line , data_emp[len(data_emp)-1]
            if line == data_emp[len(data_emp)-1]:
                res.append(sorted(data_sum_rule.iteritems(), key=operator.itemgetter(0)))
        res.append(sorted(total_data_sum_rule.iteritems(), key=operator.itemgetter(0)))    
#        print 'sao xong bay gio',res
        return res and res or []
            
    def get_rule(self):
        
        if  not self.template:
            self.get_header()
        rule = []
        sql1 = '''  select distinct(rule.id),rule.name,temp_line.sequence 
                from hr_template temp 
                left join hr_template_line temp_line on temp_line.template_id = temp.id 
                left join hr_salary_rule rule on rule.id = temp_line.name
                where temp.id = %s
                order by temp_line.sequence asc''' %(self.template[0])
        self.cr.execute(sql1)
        for line in self.cr.dictfetchall():
            dic = {
                   'id_rule': line['id'],
                   'name_rule': line['name'],
            }
            rule.append(dic)
        self.rule = rule
        return rule
    
    def get_department(self):
        result = []
        if not self.department or self.department == -1:
            self.get_header();
        if len(self.department)<=1:
            self.department.append(-1)
        sql2 = '''  select distinct(dep.id) as department_id,dep.name as department_name  
        from hr_payslip sl
        left join hr_employee emp on emp.id = sl.employee_id
        left join hr_department dep on dep.id = emp.department_id
        where sl.date_from >= '%s' 
            and sl.date_from <= '%s'
            and sl.date_to >='%s'
            and sl.date_to <='%s'
            and dep.id in %s
        order by dep.name 
  '''%(self.start_date,self.end_date,self.start_date,self.end_date,tuple(self.department))
        self.cr.execute(sql2)     
        for l in self.cr.dictfetchall():
            dic = {
                   'id_department': l['department_id'],
                   'name_department': l['department_name'],
            }
            result.append(dic)
        return result
    
        
    def get_emp(self,id_department):
        stt = 0
        result = []
        if not self.start_date:
            self.get_header();
        
        sql3 = '''  select emp.id as employee_id, emp.name_related as emp_name,sl.id as id_slip, bak.acc_number as numberbank_emp, bak.bank_name as bank_name
        from hr_payslip sl
        left join hr_employee emp on emp.id = sl.employee_id
        left join hr_department dep on dep.id = emp.department_id
        left join res_partner_bank bak on emp.bank_account_id = bak.id
        where sl.date_from >= '%s' 
            and sl.date_from <= '%s'
            and sl.date_to >='%s'
            and sl.date_to <='%s'
            and dep.id = %s
  '''%(self.start_date,self.end_date,self.start_date,self.end_date,id_department)
        self.cr.execute(sql3)
        for line in self.cr.dictfetchall():
            stt += 1
            dic = {
                   'stt': stt,
                   'id_emp': line['employee_id'],
                   'name_emp':line['emp_name'] or '' ,
                   'id_slip': line['id_slip'],
                   'numberbank_emp': line['numberbank_emp'],
                   'bank_name': line['bank_name'],
                   'name_emp_bank': line['emp_name'] and func_bodau.bo_dau_viet(line['emp_name']).upper(),
            }
            result.append(dic)
        return result
    
    
    def get_amount(self,id_department,id_slip,id_rule):
        amount = 0
        sql4 = '''  select sum(line.amount) as amount  
            from hr_payslip sl
            left join hr_payslip_line line on sl.id = line.slip_id
            left join hr_salary_rule rule on rule.id = line.salary_rule_id
            left join hr_employee emp on emp.id = sl.employee_id
            left join hr_department dep on dep.id = emp.department_id
            where sl.date_from >= '%s' 
            and sl.date_from <= '%s'
            and sl.date_to >='%s'
            and sl.date_to <='%s' 
            and dep.id = %s
            and sl.id = %s
            and rule.id = %s 
            group by rule.id
      '''%(self.start_date,self.end_date,self.start_date,self.end_date,id_department,id_slip,id_rule)
#        print 'sql4',sql4 
        self.cr.execute(sql4)  
        for line in self.cr.dictfetchall():
            amount = line['amount']
        return amount
    
    def get_date_work(self,id_slip):
        if not id_slip:
            return {}
        date_w = 0
        slip = self.pool.get('hr.payslip').browse(self.cr,self.uid,id_slip)
        if len(slip.worked_days_line_ids):
            for w in slip.worked_days_line_ids:
                if w.code == 'TIME_NORMAL':
                    date_w = w.number_of_days
                    break
        return date_w
    
    
    
    def get_date_annual(self,id_slip):
        if not id_slip:
            return {}
        date_a = 0
        slip = self.pool.get('hr.payslip').browse(self.cr,self.uid,id_slip)
        if len(slip.worked_days_line_ids):
            for a in slip.worked_days_line_ids:
                if a.code == 'TIME_LEAVE':
                    date_a = a.number_of_days
                    break
        return date_a
    
    def get_date_business(self,id_slip):
        if not id_slip:
            return {}
        date_a = 0
        slip = self.pool.get('hr.payslip').browse(self.cr,self.uid,id_slip)
        if len(slip.worked_days_line_ids):
            for a in slip.worked_days_line_ids:
                if a.code == 'TIME_BUSINESS':
                    date_a = a.number_of_days                                            
                    break
        return date_a
  
                        
    def get_rule_temp(self):
        return self.rule
    
    def get_total_work(self,id_department):
        list_emp = self.get_emp(id_department)
        total = 0
        if list_emp:
            for emp in list_emp:
                total += self.get_date_work(emp['id_slip'])
        return total
                
    def get_total_annual(self,form,id_department):
        list_emp = self.get_emp(form, id_department)
        total = 0
        if list_emp:
            for emp in list_emp:
                total += self.get_date_annual(emp['id_slip'])
        return total 
    
    def get_total_business(self,id_department):
        list_emp = self.get_emp(id_department)
        total = 0
        if list_emp:
            for emp in list_emp:
                total += self.get_date_business(emp['id_slip'])
        return total             
            
    
    def get_total_dep(self,id_department,id_rule):
        total = 0
        list_emp = self.get_emp( id_department)
        for emp in list_emp:
            temp = self.get_amount(id_department, emp['id_slip'], id_rule)
            if temp:
                total += temp
        return total
            
    def get_total_all_dep(self,id_rule):
        total = 0
        list_dep = self.get_department()
        for d in list_dep:
            temp = self.get_total_dep(d['id_department'], id_rule)
            if temp:
                total += temp
        return total
    

    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
