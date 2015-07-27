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
            'time': time,
            'get_nv':self.get_nv,
            'address': self._address,  
            'address_home': self._address_home, 
            'address_temp': self._address_temp,
            '_address_company': self._address_company,           
        })
        
    def get_nv(self,o): 
        place_of_birth = o.place_of_birth and o.place_of_birth.name  or ''    
        cmnd = o.identification_id or ''
        nc = o.identification_id_place and o.identification_id_place.name  or ''
        date_id = o.identification_id_date or ''
        ssnid = o.sinid or ''
        ssnid_place = o.sinid_place.name  or ''
        ssnid_date = o.sinid_date  or '' 
        level = ''
        if o.level_id and o.level_id:      
            level = self.pool.get('hr.recruitment.degree').read(self.cr,self.uid,[o.level_id.id],['name'])
        
        contract_emp_ids = self.pool.get('hr.contract').search(self.cr,self.uid,[('employee_id','=',o.id)])
        basic = 0
        type_hd = '' 
        if contract_emp_ids:
            sql = '''
                    select foo.basic, type.name                                  
                    from (select *,
                            row_number() over (partition by id order by date_start desc) as rownum
                            from hr_contract
                            where employee_id = %s
                            ) as foo
                        left join hr_contract_type type on type.id = foo.type_id
                    where rownum in (1); 
                    ''' %(o.id) 
            self.cr.execute(sql)
            vals = self.cr.dictfetchall()
            if vals and len(vals)>=1:
                for line in vals:
                    basic = line['basic']
                    contract_type = line['name'] or ''
                    if contract_type.upper() == 'EMPLOYEE':
                        type_hd = u'Hợp Đồng Chính Thức'
                    else:
                        if contract_type.upper() == 'WORKER':
                            type_hd = u'Hợp Đồng Cộng Tác'
                        else:    
                            if contract_type.upper() == 'SUBCONTRACTOR':
                                type_hd = u'Hợp đồng Thử Việc'
                            else:
                                type_hd = u'Hợp Đồng Học Việc'    

        dic = {
                'last_name': o.last_name and o.last_name.upper() + ' ' + o.name_related.upper() or o.name_related.upper()  ,
                'country': o.country_id and o.country_id.name or '',
                'birthday': o.birthday and time.strftime('%d/%m/%Y', time.strptime(o.birthday, '%Y-%m-%d')),
                'birthday_date': o.birthday and time.strftime('%d', time.strptime(o.birthday, '%Y-%m-%d')),
                'birthday_month': o.birthday and time.strftime('%m', time.strptime(o.birthday, '%Y-%m-%d')),
                'birthday_year': o.birthday and time.strftime('%Y', time.strptime(o.birthday, '%Y-%m-%d')),
                'job': o.job_id and o.job_id.name or '',
#                'address_home': address,
#                'address_temp': address_temp,
                'place_of_birth': place_of_birth,
                'ssnid': ssnid,
                'ssnid_date': ssnid_date,
                'ssnid_place': ssnid_place,
                'cmnd': cmnd,
                'nc': nc,
                'date_id':date_id and time.strftime('%d/%m/%Y', time.strptime(date_id, '%Y-%m-%d'))or '',
                'date_id_date':date_id and time.strftime('%d', time.strptime(date_id, '%Y-%m-%d'))or '',
                'date_id_month':date_id and time.strftime('%m', time.strptime(date_id, '%Y-%m-%d'))or '',
                'date_id_year':date_id and time.strftime('%Y', time.strptime(date_id, '%Y-%m-%d'))or '',    
                'gender': o.gender == 'male' and 'Nam' or u'Nữ',
                'level': len(level)>0 and level[0]['name'] or '',
                'religion': o.religion_id and o.religion_id.name or '',
                'ethnic': o.ethnic_id and o.ethnic_id.name or '',
#                'start_working_date': o.start_working_date and time.strftime('%d/%m/%Y', time.strptime(o.start_working_date, '%Y-%m-%d')) or '',
                'contract': o.contract_id and o.contract_id.name or '___________',
                'date_s_contract':o.contract_id and (o.contract_id.date_start and time.strftime('%d/%m/%Y', time.strptime(o.contract_id.date_start, '%Y-%m-%d')) or '' ) or '__/__/___',
                'contract_type': type_hd or '',
#                'current_basic': o.contract_id and o.contract_id.current_basic or ''
                'basic': basic or '',
               }
        return dic
    
    def _address_company(self, partner, separator=', ', country=True, state=True, city=True, street=True):
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
   
    def _address(self,o):
        address = ''
        street = o.address_id and o.address_id.street or ''
        city = o.address_id and o.address_id.city or ''
        state = o.address_id and (o.address_id.state_id and o.address_id.state_id.name or '') or '' 
        if street:
            address += street 
        if city:
            address += ',' + city 
        if state:
            address += ',' + state 
        return address
    
    def _address_home(self,o):
        address = ''
        street = o.address_home_id and o.address_home_id.street or ''
        city = o.address_home_id and o.address_home_id.city or ''
        state = o.address_home_id and (o.address_home_id.state_id and o.address_home_id.state_id.name or '') or '' 
        if street:
            address += street 
        if city:
            address += ',' + city 
        if state:
            address += ',' + state 
        return address
    
    def _address_temp(self,o):
        address = ''
        street = o.address_temp_id and o.address_temp_id.street or ''
        city = o.address_temp_id and o.address_temp_id.city or ''
        state = o.address_temp_id and (o.address_temp_id.state_id and o.address_temp_id.state_id.name or '') or '' 
        if street:
            address += street 
        if city:
            address += ',' + city 
        if state:
            address += ',' + state 
        return address
        

    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
