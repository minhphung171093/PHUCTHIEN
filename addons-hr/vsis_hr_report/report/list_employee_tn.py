##############################################################################
#
# Copyright (c) 2008-2011 Alistek Ltd (http://www.alistek.com) All Rights Reserved.
#                    General contacts <info@alistek.com>
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 3
# of the License, or (at your option) any later version.
#
# This module is GPLv3 or newer and incompatible
# with OpenERP SA "AGPL + Private Use License"!
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##############################################################################

from report import report_sxw
from report.report_sxw import rml_parse


class list_employee_tn(report_sxw.rml_parse):
    def __init__(self, cr, uid, ids, data, context):
        super(list_employee_tn, self).__init__(cr, uid, ids, data, context)
        self.sott = 0        
        self.val_col = []
        self.list_product = []
        self.localcontext.update({
            'time': time,
            'get_gd': self.get_gd,
            'convert':self.convert,
            'birthday': self.birthday, 
            'get_department': self.get_department,           
        })
        context.update(self.localcontext)
        
    def convert(self,amount):
        amt_vn = amount_to_text_vn.amount_to_text_vn(amount,'VND');
        return amt_vn
    
    def get_department(self):
        result = []
        print 'vao ham roi'
#        if department_id: 
        date_start = time.strftime('%Y-%m-%d')
        department = self.pool.get('hr.department').browse(self.cr,self.uid,department_id)
        for d in department:
            sql = ''' select emp.id from hr_employee emp where emp.department_id = %s  ''' %(d.id)
            self.cr.execute(sql)
            ids = map(lambda x: x[0], self.cr.fetchall())
            if len(ids)>=1:
                dic = {
                       'id': d.id or None,
                       'name': d.name or ''
                }
                result.append(dic)
        return result
    
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
        
    def get_gd(self,form,deparment_id):
        ids = self.pool.get('hr.employee').search(self.cr,self.uid,[])
        list_employee = self.pool.get('hr.employee').browse(self.cr,self.uid,ids)
        result =[]
        stt = 0
#        date_start = time.strftime('%Y-%m-%d')
        for id in list_employee:
            month =0
            date_start = time.strftime('%Y-%m-%d')
            dic = {}
            name = id.last_name and id.last_name + ' ' + id.name_related or id.name_related 
            address = ''
            street = id.address_home_id and id.address_home_id.street or ''
            city = id.address_home_id and id.address_home_id.city or ''
            state = id.address_home_id and (id.address_home_id.state_id and id.address_home_id.state_id.name or '') or ''
            if street:
                address += street + ','
            if city:
                address += city + ','
            if state:
                address += state
            if id.create_code_date:
                date_start = id.create_code_date
            date_end = time.strftime('%Y-%m-%d')
            month = self.number_month(date_start,date_end)
#            print 'so thang ne',month
            level = ''
            if id.level_id and id.level_id.id:      
                level = self.pool.get('hr.recruitment.degree').read(self.cr,self.uid,[id.level_id.id],['name'])
#            print 'month', month
            stop_working_date = id.stop_working_date
            if not stop_working_date or  stop_working_date> date_end:
                if month >= int(form['number_month']) :
                    if id.department_id and  id.department_id.id == deparment_id:
                        stt +=1  
                        dic.update({
                                'id': id.id,
                                'stt': stt,
                                'code': id.code or '',
                                'name':name,
                                'month':month or 0,
                                'birthday': id.birthday or '',
                                'department': id.department_id and id.department_id.name or '',
                                'job':id.job_id and id.job_id.name or '',
                                'address': address,
                                'religion': id.religion_id and id.religion_id.name or '',
                                'start_date':date_start,
                                'level': len(level)>0 and level[0]['name'] or '',
                                'id_cm': id.identification_id  or '',
                                'id_place': id.identification_id_place and id.identification_id_place.name or '',
                                'id_date': id.identification_id_date and time.strftime('%d/%m/%Y', time.strptime(id.identification_id_date, '%Y-%m-%d')) or '',
                                'start_working_date': id.create_code_date and time.strftime('%d/%m/%Y', time.strptime(id.create_code_date, '%Y-%m-%d')) or '',
                               })
                        result.append(dic) 
        return result
            
    def birthday(self,emp,male):
        birthday  = ''
        employee = self.pool.get('hr.employee').read(self.cr,self.uid,emp,['gender','birthday'])
        if male == employee['gender']:
            birthday = employee['birthday'] and time.strftime('%d/%m/%Y', time.strptime(employee['birthday'], '%Y-%m-%d'))or '', 
        return birthday          
    
    


