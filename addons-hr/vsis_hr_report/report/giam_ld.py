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
        self.start_date = False
        self.end_date = False
        self.get_company(cr, uid)
        
        self.sott = 0
        self.female = 0
        self.hcm =0 
        self.state_tinh =0       
        self.val_col = []
        self.list_product = []
        self.flag = 0
        
        self.localcontext.update({
            'get_company_name':self.get_company_name,
            'get_company_address':self.get_company_address,       
            'get_start_date':self.get_start_date,
            'get_end_date':self.get_end_date,       
            'time': time,
            'convert':self.convert,
            'number_month':self.number_month,
            'birthday':self.birthday,
            'state':self.state,
            'state_hcm':self.state_hcm, 
            'address':self._address,
            'sum_gender': self.sum_gender,
            'sum_city':self.sum_city,
            'stt':self.stt,  
            'nu':self.nu,
            'date_cur': self.date_cur,
            'tinh':self.tinh,
            'hcm':self.hcm_t,
            'gender_tinh':self.gender_tinh,
            'get_nv':self.get_nv,  
            'sum_type': self.sum_type,
            'sum_type_12':self.sum_type_12,
            'sum_type_36':self.sum_type_36,
            'get_nn': self.get_nn,
            'sum_lydo': self.sum_lydo, 
            'sum_lydo_2':self.sum_lydo_2,
            'sum_sld':self.sum_sld,
            'ngay': self.ngay,
        })
    def get_header(self):
        wizard_data = self.localcontext['data']['form']
        self.start_date = wizard_data['date_start'] or False
        self.end_date = wizard_data['date_stop'] or False
        
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
        n =  datetime(int(year_e),int(month_e),int(date_e))- datetime(int(year_s),int(month_s),int(date_s))  
        n = n.days
        month = divmod(n,30) 
        return month[0]
    
    def conver_strdate_to_date_or_datetime(self,strdate,result):
        if result=="date":
            dt_date=datetime.date(int(strdate[0:4]),int(strdate[5:7]),int(strdate[8:10]))
        else:
            dt_date=datetime.datetime(int(strdate[0:4]),int(strdate[5:7]),int(strdate[8:10]))
        return dt_date
    
    
    def get_nv(self):
        
        
        res = [] 
        month =  0
        stt = 0 
        date_start_contract = '' 
        NH = ''
        HH = ''
        TV = ''
        MV = ''
        BV = ''
        ST = ''
        KH = '' 
        if not self.start_date :
            self.get_header()
            
        date_start = self.start_date 
        date_stop = self.end_date
        sql= '''select emp.id,emp.last_name 
                from hr_employee emp
                where emp.stop_working_date >='%s' and emp.stop_working_date <='%s' ''' %(date_start,date_stop)

        self.cr.execute(sql)  
        
        for id in self.cr.dictfetchall():          
            stt += 1 
            if id['id']:
                obj_emp = self.pool.get('hr.employee').browse(self.cr,self.uid,id['id'])
                name = obj_emp.name
            last_name = id['last_name'] and id['last_name']+ ' ' + name or name   
            
            address = ''
            street = obj_emp.address_home_id.street
            city = obj_emp.address_home_id.city
            if street:
                address += street+ ' '
            if city:
                address += city
            
            cur_address = ''
            street = obj_emp.address_temp_id.street
            city = obj_emp.address_temp_id.city
            if street:
                cur_address += street+ ' '
            if city:
                cur_address += city
                
            state = obj_emp.address_home_id and (obj_emp.address_home_id.state_id \
                                            and obj_emp.address_home_id.state_id.code or None)or ''
           
            major =''
            vals = False
            if obj_emp.contract_id.id:
                self.cr.execute("select min(date_start) as date_start from hr_contract where id = %s",(obj_emp.contract_id.id,))        
                vals = self.cr.dictfetchall()
            if vals:
                for line in vals:
                    date_start_contract = line['date_start']
                    
            if obj_emp.reason_id.type == 'NH':
                NH = 'x'
            else:
                if obj_emp.reason_id.type == 'HH':
                    HH = 'x'
                else:
                    if obj_emp.reason_id.type == 'TV':
                        TV = 'x'
                    else:
                        if obj_emp.reason_id.type == 'MV':
                            MV = 'x'
                        else:
                            if obj_emp.reason_id.type == 'BV':
                                BV = 'x'
                            else:
                                if obj_emp.reason_id.type == 'ST':
                                    ST = 'x'
                                else:
                                    KH = 'x' 

            contract = obj_emp.contract_id.name
            code = obj_emp.emp_code
            type_code = obj_emp.contract_id.type_id
            if type_code:
                type = type_code.name
            department = obj_emp.department_id.name
            gender = obj_emp.gender
            place_of_birth = obj_emp.place_of_birth and obj_emp.place_of_birth.name or ''
            date_start1 = obj_emp.contract_id and obj_emp.contract_id.date_start or ''
            date_end = obj_emp.contract_id and obj_emp.contract_id.date_end or ''
            level = ''
            if obj_emp.level_id and obj_emp.level_id:      
                level = self.pool.get('hr.recruitment.degree').read(self.cr,self.uid,[obj_emp.level_id.id],['name'])
   
            if date_end:
                month = self.number_month(date_start,date_end)   
            res.append({
                        'stt': stt,
                        'id': id['id'],
                        'gender':gender,
                        'name': last_name,
                        'major': major or '',
                        'level': len(level)>0 and level[0]['name'] or '',
                        'place_of_birth': place_of_birth,
                        'contract': contract,
                        'date_start': date_start1 and time.strftime('%d/%m/%Y', time.strptime(date_start1, '%Y-%m-%d')),
                        'date_end': date_end ,
                        'job':obj_emp.job_id and obj_emp.job_id.name or '',
                        'address': address,
                        'time_contract': month or 0,
                        'cur_address': cur_address or '',
                        'state': state,
                        'code': code,
                        'NH': NH,
                        'HH': HH,
                        'TV': TV,
                        'MV': MV,
                        'BV': BV,
                        'ST': ST,
                        'KH': KH, 
                        'working_date':date_start_contract and time.strftime('%d/%m/%Y', time.strptime(date_start_contract, '%Y-%m-%d'))or '',
                        'reason':obj_emp.reason_id and obj_emp.reason_id.type or '',
                        })
        return res 
    
    def get_nn(self,emp,reason):
        if emp['reason']== reason:
            self.flag +=1
            return 'x'
        else:
            return ''
        
        
    def sum_lydo(self): 
        return self.flag  
    
    def sum_lydo_2(self,reason):
        dem =0
        ds = self.get_nv()
        for id in ds:
            if id['reason']== reason:
                dem +=1
        return dem   
                
         
    
    def stt(self):
        return self.sott     
    
    def nu(self):
        return self.female
    
    def hcm_t(self):
        return self.hcm
    
    def tinh(self):
        return self.state_tinh
    
    def date_cur(self):
        dic = {}
        from datetime import datetime
        date_current = str(datetime.now())
        date_cur = self.conver_strdate_to_date_or_datetime(date_current, 'date')
        date_cur = str(date_cur)
        date = time.strftime('%d', time.strptime(date_cur, '%Y-%m-%d'))
        month = time.strftime('%m', time.strptime(date_cur, '%Y-%m-%d')) 
        year = time.strftime('%Y', time.strptime(date_cur, '%Y-%m-%d'))
        dic = {
               'date': date,
               'month': month,
               'year': year,
        }
        return dic
         
    def birthday(self,emp,male):
        birthday  = ''
        employee = self.pool.get('hr.employee').read(self.cr,self.uid,emp,['gender','birthday'])
        if male == employee['gender']:
            birthday = employee['birthday'] and time.strftime('%d/%m/%Y', time.strptime(employee['birthday'], '%Y-%m-%d'))or '', 
        return birthday 
   
    def state(self,emp,state):
        dc = ''
        employee = self.pool.get('hr.employee').browse(self.cr,self.uid,emp)
        code = employee and (employee.address_home_id \
                             and (employee.address_home_id.state_id \
                                  and employee.address_home_id.state_id.code \
                                   or None)\
                                        or None) \
                                          or ''
        if code and code != 'HCM': 
            dc = employee and (employee.address_home_id \
                             and (employee.address_home_id.state_id \
                                  and employee.address_home_id.state_id.name \
                                   or None)\
                                        or None) \
                                          or ''
            
        return dc
    
    def state_hcm(self,emp,state):
        dc = ''
        employee = self.pool.get('hr.employee').browse(self.cr,self.uid,emp)
        code = employee and (employee.address_home_id \
                             and (employee.address_home_id.state_id \
                                  and employee.address_home_id.state_id.code \
                                   or None)\
                                        or None) \
                                          or ''  
        if code and code == 'HCM': 
            dc = 'x'
        return dc
    
    
    def contract_type(self,emp,cat):
        emp = self.pool.get('hr.employee').browse(self.cr,self.uid,emp)
        contract_id = emp and (emp.contract_id and emp.contract_id.id or None)or None
        contract = self.pool.get('hr.contract').browse(self.cr,self.uid,contract_id)
        number = 0
        k_han = ''
        if contract:
            date_end = contract.date_end
            if not date_end:
                k_han = 1
        return k_han    
    
    
    def contract_type_12(self,emp,cat):
        emp = self.pool.get('hr.employee').browse(self.cr,self.uid,emp)
        contract_id = emp and (emp.contract_id and emp.contract_id.id or None)or None
        contract = self.pool.get('hr.contract').browse(self.cr,self.uid,contract_id)
        number = 0
        m_hai = ''
        if contract:
            date_start = contract.date_start
            date_end = contract.date_end
            date_s = date_start[8:10]
            month_s = date_start[5:7]
            year_s = date_start[0:4]
               
            if date_end: 
                date_e = date_end[8:10]
                month_e = date_end[5:7] 
                year_e = date_end[0:4]
            else:
                date_end = date_start 
                date_e = date_end[8:10]
                month_e = date_end[5:7] 
                year_e = date_end[0:4]
            n =  datetime.datetime(int(year_e),int(month_e),int(date_e))- datetime.datetime(int(year_s),int(month_s),int(date_s))  
            n = n.days
            month = divmod(n,30) 
            
            if cat == 12:
                if month[0]>0 and month[0]<=12:
                    number = month[0]
                    m_hai = str(number) + ' month'
                    m_hai = 'x'
        return m_hai 
    
    def contract_type_36(self,emp,cat):
        emp = self.pool.get('hr.employee').browse(self.cr,self.uid,emp)
        contract_id = emp and (emp.contract_id and emp.contract_id.id or None)or None
        contract = self.pool.get('hr.contract').browse(self.cr,self.uid,contract_id)
        number = 0
        b_sau = ''
        if contract:
            date_start = contract.date_start
            date_end = contract.date_end
            date_s = date_start[8:10]
            month_s = date_start[5:7]
            year_s = date_start[0:4]
            
            if date_end: 
                date_e = date_end[8:10]
                month_e = date_end[5:7] 
                year_e = date_end[0:4]
            else:
                date_end = date_start 
                date_e = date_end[8:10]
                month_e = date_end[5:7] 
                year_e = date_end[0:4]
            n =  datetime.datetime(int(year_e),int(month_e),int(date_e))- datetime.datetime(int(year_s),int(month_s),int(date_s))  
            n = float(n.days)
            month = divmod(n,30) 
            if cat==36:
                if month[0]>12 and month[0]<= 36:
                    number = month[0]
                    b_sau = str(number) + ' month'   
        return number
    
    def gender_tinh(self,gender,state):
        count = 0
        list_emp = self.get_nv()
        for em in list_emp:
            if em['gender'] == gender and em['code'] != state:
                count += 1
        return count
    
    def sum_gender(self,gender):
        count = 0
        list_emp = self.get_nv()
        for em in list_emp:
            if em['gender'] == gender:
                count += 1
        self.female = count
        return count
    
    def sum_city(self,state):
        count = 0
        count_1 = 0
        list_emp = self.get_nv()
        for em in list_emp:
            if em['state'].upper() == 'HCM':
                count += 1  
            else:
                count_1 +=1
        self.state_hcm = count
        self.state_tinh = count_1
        return {'count':count,'count_1':count_1}
    
    def sum_type(self,cat):
        count = 0
        male = 0
        female = 0
        dic = {'count': 0,'male': 0,'female': 0}
        list_emp = self.get_nv()
        for em in list_emp:
            flag = self.contract_type(em['id'], cat)
            if flag:
                count += 1
                if em['gender'] =='male':
                    male +=1
                else:
                    female +=1 
            dic = {'count': count,'male': male,'female': female}
        return dic
    
    def sum_type_12(self,cat):
        count = 0
        male = 0
        female = 0
        dic = {'count': 0,'male': 0,'female': 0}
        list_emp = self.get_nv(form)
        for em in list_emp:
            flag = self.contract_type_12(em['id'], cat)
            if flag:
                count += 1
                if em['gender'] =='male':
                    male +=1
                else:
                    female +=1 
            dic = {'count': count,'male': male,'female': female} 
        return dic
    
    def sum_type_36(self,cat):
        count = 0
        male = 0
        female = 0
        dic = {'count': 0,'male': 0,'female': 0}
        list_emp = self.get_nv()
        for em in list_emp:
            flag = self.contract_type_36(em['id'], cat)
            if flag:
                count += 1
                if em['gender'] =='male':
                    male +=1
                else:
                    female +=1 
            dic = {'count': count,'male': male,'female': female} 
        return dic
    
    def ngay(self,form):
#        period = self.pool.get('gs.hr.period').read(self.cr,self.uid,form['period_id'],['date_start','date_stop'])
        date_start = form['date_start']
        date_stop = form['date_stop']
#        if not form['period_id_end']:
#            date_e = date_stop
#        else:
#            period_end = self.pool.get('gs.hr.period').read(self.cr,self.uid,form['period_id_end'],['date_stop'])
#            date_stop_end = period_end['date_stop']
#            date_e = date_stop_end
        dic = {
            'date_s':date_start and time.strftime('%d/%m/%y', time.strptime(date_start , '%Y-%m-%d')) or '',
            'date_e': date_stop and time.strftime('%d/%m/%y', time.strptime(date_stop , '%Y-%m-%d')) or '',
            }
        return  dic
        
        
    def sum_sld(self):
        count = 0
        count_nu = 0
        count_tinh = 0
        count_tinh_nu = 0
        count_ko_th = 0
        count_ko_th_nu = 0
        count_36 = 0
        count_12 = 0
        count_36_nu = 0
        count_12_nu = 0
        
        date_start = self.start_date
        date_stop = self.end_date

        ids_emp = self.pool.get('hr.employee').search(self.cr,self.uid,['|',('stop_working_date','=',None),('create_code_date','<=',date_stop)])

        if ids_emp:    
            obj_emp = self.pool.get('hr.employee').browse(self.cr,self.uid,ids_emp)
            for e in obj_emp:
                if e.contract_id:
                    sql = '''
                                drop table if exists get_contract;
                                drop table if exists get_contract_del;
                               
                                create temporary table get_contract on commit drop as
                                select date_part('day', date_start::date) as day,
                                        date_part('month', date_start::date) as month,
                                        date_part('year', date_start::date) as year,                                    *
                                from (select *,
                                        row_number() over (partition by id order by date_start desc) as rownum
                                        from hr_contract
                                        where id = %s
                                            and '%s'::date between date_start and case when date_end is null then '2100-12-31'::date else date_end end
                                            
                                        ) as foo
                                where rownum in (1,2);
                                
                                create temporary table get_contract_del on commit drop as
                                select id from get_contract 
                                where rownum = 1 
                                    and day >= 15
                                    and month = date_part('month', '%s'::date)
                                    and year = date_part('year', '%s'::date);
                                    
                                delete from get_contract where id in (select id from get_contract_del); 
                                delete from get_contract where id not in (select id from get_contract_del) and rownum = 2;                 
                                
                                select dur.month, ct.date_start 
                                from get_contract ct
                                    left join hr_contract_duration dur on dur.id = ct.duration_type;
                                
                                ''' %(e.contract_id.id,date_start,date_start,date_start) 
                    self.cr.execute(sql)
                    dic = self.cr.dictfetchall()
                    if dic and len(dic)>=1:
                        count +=1  
                        if e.gender and e.gender.lower() =='female' :
                            count_nu +=1 
                        state = e.address_home_id and (e.address_home_id.state_id \
                                                       and e.address_home_id.state_id.code or '') or '' 
                        if state and state.lower() != 'hcm':
                            count_tinh +=1 
                            if e.gender and e.gender.lower() == 'female':
                                count_tinh_nu += 1
                        
                        for line in dic:
                            if int(line['month']) == 0 or int(line['month']) > 36:
                                count_ko_th +=1 
                                if e.gender and e.gender.lower() == 'female':
                                    count_ko_th_nu +=1
                            else:
                                if int(line['month']) >= 12 and int(line['month']) <= 36:
                                    count_36 +=1
                                    if e.gender and e.gender.lower() == 'female':
                                        count_36_nu +=1 
                                else:
                                    count_12 +=1
                                    if e.gender and e.gender.lower() == 'female':
                                        count_12_nu +=1       
                            
                            
                                                           
            return {
                    'count':count,
                    'count_nu':count_nu,
                    'count_tinh': count_tinh,
                    'count_tinh_nu':count_tinh_nu,
                    'count_ko_th': count_ko_th,
                    'count_ko_th_nu': count_ko_th_nu,
                    'count_36': count_36,
                    'count_12': count_12,
                    'count_36_nu': count_36_nu,
                    'count_12_nu': count_12_nu,
                    }
    
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

    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
