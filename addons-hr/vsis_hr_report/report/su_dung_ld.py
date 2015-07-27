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
        self.sott = 0
        self.female = 0
        self.hcm =0 
        self.state_tinh =0         
        self.val_col = []
        self.list_product = []
        
        self.localcontext.update({
            'time': time,
            'convert':self.convert,
            'birthday':self.birthday,
            'state': self.state, 
            'state_hcm': self.state_hcm,
            'sum_gender': self.sum_gender,
            'sum_city':self.sum_city,
            'sum_type': self.sum_type,
            'sum_type_12':self.sum_type_12,
            'sum_type_36':self.sum_type_36,
            'address': self._address,
            'stt':self.stt,
            'nu':self.nu,
            'date_cur': self.date_cur,
            'tinh':self.tinh,
            'hcm':self.hcm_t,
            'gender_tinh':self.gender_tinh,
            'get_nv': self.get_nv,
            'ngay': self.ngay,
            'sum_sld': self.sum_sld,
        })
    
    def get_header(self):
        wizard_data = self.localcontext['data']['form']
        
        self.start_date = wizard_data['date_start'] or False
        self.end_date = wizard_data['date_stop'] or False
        
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
            dt_date=date(int(strdate[0:4]),int(strdate[5:7]),int(strdate[8:10]))
        else:
            dt_date=datetime(int(strdate[0:4]),int(strdate[5:7]),int(strdate[8:10]))
        return dt_date
    

                       
    def get_nv(self):
        self.get_header()
        date_start1 = self.start_date
        date_stop = self.end_date
        
        ids_emp = self.pool.get('hr.employee').search(self.cr,self.uid,['|',('stop_working_date','=',None),('create_code_date','<=',date_stop)])
        if ids_emp:    
            obj_emp = self.pool.get('hr.employee').browse(self.cr,self.uid,ids_emp)  

            month = 0
            res = []
            stt = 0
            amount = 0
            for id in obj_emp: 
                ###
                # Get contract
                kth = ''
                kth12 = ''
                kth36 = ''
                date_start = ''
                if id.contract_id:
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
                                        and trial_date_start is null
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
                            
                            select dur.month, ct.date_start, ct.basic 
                            from get_contract ct
                                left join hr_contract_duration dur on dur.id = ct.duration_type;
                            
                            ''' %(id.contract_id.id,date_start1,date_start1,date_start1) 
                    self.cr.execute(sql)
                    dic = self.cr.dictfetchall()
                    if dic and len(dic)>=1:
                        for line in dic:
                            if int(line['month']) == 0:
                                kth = 'x'
                            else:
                                if int(line['month']) >= 12 and int(line['month']) <= 36:
                                    kth36 = str(int(line['month']/12)) + u' năm' 
                                else:
                                    kth12 = str(int(line['month'])) + u' tháng'
                            date_start = line['date_start']
                            amount = line['basic']
                ###
                        address = ''
                        street = id.address_home_id.street
                        city = id.address_home_id.city
                        if street:
                            address += street+ ' '
                        if city:
                            address += city
                        
                        cur_address = ''
                        street = id.address_temp_id.street
                        city = id.address_temp_id.city
                        if street:
                            cur_address += street+ ' '
                        if city:
                            cur_address += city
                            
                        state = id.address_home_id and (id.address_home_id.state_id \
                                                        and id.address_home_id.state_id.code or None)or ''
                       
                        major =''
                        # for m in id.major_ids:
                            # if major:
                                # major = major + ',' +m.name
                            # else: 
                                # major = m.name
                              
                        contract = id.contract_id.name
                        code = id.emp_code
                        type_code = id.contract_id.type_id
                        if type_code:
                            type = type_code.name
                        level = ''
                        levels = ''
                        if id.level_id and id.level_id:      
                            levels = self.pool.get('hr.recruitment.degree').read(self.cr,self.uid,[id.level_id.id],['name'])
                        if levels:    
                            try:
                                b = int(levels[0]['name'][0])+1
                                level = levels[0]['name']
                                major = ''
                            except Exception, e:
                                level = '' 
                                major = levels[0]['name']
                                levels[0]['name']
                            
                        place_of_birth = id.place_of_birth and id.place_of_birth.name or ''
                        date_start_1 = id.contract_id and id.contract_id.date_start or ''
                        date_end = id.contract_id and id.contract_id.date_end or ''
                        if date_end:
                            month = self.number_month(date_start_1,date_end)   
                        stt += 1
                        res.append({
                            'stt': stt,
                            'id': id.id,
                            'gender':id.gender,
                            'name': id.last_name and id.last_name+ ' ' + id.name or id.name ,
                            'major': major or '',
                            'level': level or '',
                            'kth': kth,
                            'kth12': kth12,
                            'kth36': kth36,
                            'place_of_birth': place_of_birth,
                            'contract': contract,
                            'date_start': date_start and time.strftime('%d/%m/%Y', time.strptime(date_start, '%Y-%m-%d')),
                            'date_end': date_end ,
                            'job':id.job_id and id.job_id.name or '',
                            'address': address,
                            'time_contract': month or 0,
                            'amount': int(amount) or 0,
                            'cur_address': cur_address or '',
                            'state': state,
                            'code': code,
                            })
               
        return res
    
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
    
    def sum_sld(self,form):
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
#        period = self.pool.get('gs.hr.period').read(self.cr,self.uid,form['period_id'],['date_start','date_stop'])
        date_start = form['date_start']
        date_stop = form['date_stop']
#        if not form['period_id_end']:
        
        ids_emp = self.pool.get('hr.employee').search(self.cr,self.uid,['|',('stop_working_date','=',None),('stop_working_date','<=',date_stop)])
    #        else:
    #            period_end = self.pool.get('gs.hr.period').read(self.cr,self.uid,form['period_id_end'],['date_stop'])
    #            date_stop_end = period_end['date_stop']
    #            ids_emp = self.pool.get('hr.employee').search(self.cr,self.uid,['|',('stop_working_date','=',None),('stop_working_date','<=',date_stop_end)])
        if ids_emp:
            obj_emp = self.pool.get('hr.employee').browse(self.cr,self.uid,ids_emp)
            for e in obj_emp:
    #            if not form['period_id_end']:
    #                if e.create_code_date >= date_start and e.create_code_date < date_stop:
                count +=1  
                if e.gender =='female' :
                    count_nu +=1 
                state = e.address_home_id and (e.address_home_id.state_id \
                                               and e.address_home_id.state_id.code or '') or '' 
                if state != 'hcm':
                    count_tinh +=1 
                    if e.gender == 'female':
                        count_tinh_nu += 1
                if e.contract_id :
                    if not e.contract_id.date_end:
                        count_ko_th +=1 
                        if e.gender == 'female':
                            count_ko_th_nu +=1
                    else:
                        date_start = e.contract_id.date_start
                        date_end = e.contract_id.date_end
                        
                        date_s = date_start[8:10]
                        month_s = date_start[5:7]
                        year_s = date_start[0:4]    
                        
                        date_e = date_end[8:10]
                        month_e = date_end[5:7]
                        year_e = date_end[0:4]
                        
                        n =  datetime.datetime(int(year_e),int(month_e),int(date_e))- datetime.datetime(int(year_s),int(month_s),int(date_s))  
                        n = n.days
                        n = float(n)
                        month = divmod(n,30) 
                        if month[0]>12 and month[0]<= 36:
                            count_36 +=1
                            if e.gender == 'female':
                                count_36_nu +=1
                        elif month[0]>0 and month[0]<= 12:
                            count_12 +=1
                            if e.gender == 'female':
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
        
    def date_cur(self):
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
    
    def stt(self):
        return self.sott     
    
    def nu(self):
        return self.female
    
    def hcm_t(self):
        return self.hcm
    
    def tinh(self):
        return self.state_tinh
        
    
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
        # if code and code == 'hcm' and state == 'hcm':
            # dc = employee and (employee.address_home_id \
                             # and (employee.address_home_id.state_id \
                                  # and 'x' \
                                   # or None)\
                                        # or None) \
                                          # or ''
        return dc
    
    def sum_gender(self,form,gender):
        count = 0
        list_emp = self.get_nv(form)
        for em in list_emp:
            if em['gender'] == gender:
                count += 1
        self.female = count
        return self.female
    
    def gender_tinh(self,form,gender,state):
        count = 0
        list_emp = self.get_nv(form)
        for em in list_emp:
            if em['gender'] == gender and em['code'] != state:
                count += 1
        return count
        
    
    def sum_city(self,form,state):
        count = 0
        count_1 = 0
        list_emp = self.get_nv(form)
        for em in list_emp:
            if em['state'] == 'hcm':
                count += 1  
            else:
                count_1 +=1
        self.state_hcm = count
        self.state_tinh = count_1
        return {'count':count,'count_1':count_1}
    
    def sum_type(self,form,cat):
        count = 0
        male = 0
        female = 0
        dic = {'count': 0,'male': 0,'female': 0}
        list_emp = self.get_nv(form)
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
    
    def sum_type_12(self,form,cat):
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
    
    def sum_type_36(self,form,cat):
        count = 0
        male = 0
        female = 0
        dic = {'count': 0,'male': 0,'female': 0}
        list_emp = self.get_nv(form)
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
