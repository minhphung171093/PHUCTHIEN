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
        self.start_date = False
        self.end_date = False
        self.total_mienphi = 0.0
        self.total_thucthu =0.0
        self.total_bp0 = 0.0
        self.total_bp1 = 0.0
        self.section_id = False
        self.section_name = ''
        self.other_section_name = []
        self.other_section_id = []
        self.localcontext.update({
            'get_line':self.get_line,
            'get_start_date':self.get_start_date,
            'get_end_date':self.get_end_date,
            'get_company_name':self.get_company_name,
            'get_company_address':self.get_company_address,
            'get_company_vat':self.get_company_vat,
            'get_vietname_datetime':self.get_vietname_datetime,
            
            'get_total':self.get_total,
            
            'get_product_qty':self.get_product_qty,
            
            'get_total_qty':self.get_total_qty,
            
            'get_total_mienphi':self.get_total_mienphi,
            'get_total_thucthu':self.get_total_thucthu,
            'get_total_bp0':self.get_total_bp0,
            'get_total_bp1':self.get_total_bp1,
            
            'get_team_name': self.get_team_name,
            'get_other_team_name': self.get_other_team_name,
        })
    
    def get_team_name(self):
        if not len(self.section_name):
            sql ='''
            SELECT name
            FROM crm_case_section
            WHERE id = %s
            '''%(self.section_id)
            self.cr.execute(sql)
            for i in self.cr.dictfetchall():
                self.section_name = i['name']
        return self.section_name
    
    def get_other_team_name(self, stt_bo_phan=False):
        if not len(self.other_section_name):
            sql ='''
            SELECT id,code,name
            FROM crm_case_section
            WHERE id <> %s
            '''%(self.section_id)
            self.cr.execute(sql)
            for i in self.cr.dictfetchall():
                self.other_section_name.append(i['name'])
                self.other_section_id.append(i['id'])
        return self.other_section_name[stt_bo_phan]
    
    def get_header(self):
        wizard_data = self.localcontext['data']['form']
        self.company_id = wizard_data['company_id'] and wizard_data['company_id'][0] or False
        self.get_company(self.company_id)
        
        self.start_date = wizard_data['from_date']
        self.end_date = wizard_data['to_date']
        self.section_id =wizard_data['section_id'] and wizard_data['section_id'][0] or False
        return True
    
    def get_total(self):
        self.get_payment()
        self.conlai = self.total - self.cash - self.banks
        return self.total
    
    def get_conlai(self):
        return self.conlai
    
    def get_start_date(self):
        return self.get_vietname_datetime(self.start_date) 
    
    def get_end_date(self):
        return self.get_vietname_datetime(self.end_date) 
    
    def get_vietname_date(self, date):
        if not date:
            return ''
        date = datetime.strptime(date, DATE_FORMAT)
        return date.strftime('%d/%m/%Y')
    
    def get_vietname_datetime(self, date):
        if not date:
            return ''
        date = datetime.strptime(date, DATETIME_FORMAT)
        user_pool = self.pool.get('res.users')
        date_user_tz = user_pool._convert_user_datetime(self.cr, self.uid, date.strftime(DATETIME_FORMAT))
        date_user_tz = date_user_tz.strftime('%d/%m/%Y')
        return date_user_tz
    
    def get_company(self, company_id):
        if company_id:
            company_obj = self.pool.get('res.company').browse(self.cr, self.uid,company_id)
            self.company_name = company_obj.name or ''
            self.company_address = company_obj.street or ''
            self.vat = company_obj.vat or ''
        return True
    
    def get_company_name(self):
        self.get_header()
        return self.company_name
    
    def get_company_address(self):
        return self.company_address     
    
    def get_company_vat(self):
        return self.vat
    
    def get_product_qty(self, product_id, part_or_team_id, check_type, price_unit, stt_bo_phan=False):
        if check_type == 1:
            sql ='''
                select sum(qty)  qty
                FROM pos_order_line pol inner join pos_order pos on pos.id = pol.order_id and pos.partner_id = %s and pos.section_id = %s and pos.state not in ('cancel')
                WHERE
                pol.product_id = %s 
                and pol.section_id = %s
                and pos.date_order between '%s' and '%s'
                and pol.price_unit = %s
            '''%(part_or_team_id,self.section_id,product_id,self.section_id,self.start_date,self.end_date,price_unit)
        else:
            sql ='''
                select sum(qty)  qty
                FROM pos_order_line pol inner join pos_order pos on pos.id = pol.order_id and pos.section_id = %s and pos.state not in ('cancel')
                WHERE
                pol.product_id =%s 
                and pol.section_id = %s
                and pos.date_order between '%s' and '%s'
                and pol.price_unit = %s
            '''%(self.other_section_id[stt_bo_phan],product_id,self.section_id,self.start_date,self.end_date,price_unit)
        self.cr.execute(sql)
        for i in self.cr.dictfetchall():
            return i['qty'] or 0.0
        return 0.0
    
    def get_total_qty(self, part_or_team_id, check_type, stt_bo_phan=False):
        if check_type == 1:
            sql ='''
                select sum(qty)  qty
                FROM pos_order_line pol inner join pos_order pos on pos.id = pol.order_id and pos.partner_id = %s 
                    and pos.section_id = %s and pos.state not in ('cancel')
                WHERE pol.section_id  = %s
                and pos.date_order between '%s' and '%s'
            '''%(part_or_team_id,self.section_id,self.section_id,self.start_date,self.end_date)
        else:
            sql ='''
                select sum(qty)  qty
                FROM pos_order_line pol inner join pos_order pos on pos.id = pol.order_id 
                    and pos.section_id = %s
                    and pos.state not in ('cancel')
                WHERE pol.section_id = %s
                and pos.date_order between '%s' and '%s'
            '''%(self.other_section_id[stt_bo_phan],self.section_id,self.start_date,self.end_date)
        self.cr.execute(sql)
        for i in self.cr.dictfetchall():
            return i['qty'] or 0.0
        return 0.0
    
    def get_total_mienphi(self):
        return self.total_mienphi or 0.0
    
    def get_total_thucthu(self):
        return self.total_thucthu or 0.0
    
    def get_total_bp0(self):
        return self.total_bp0 or 0.0
    
    def get_total_bp1(self):
        return self.total_bp1 or 0.0
    
    def get_line(self):
        res=[]
        if not self.end_date:
            self.get_header()
        sql ='''
            SELECT product_id,name_template,name uom_name,price_unit,
                   sum(qty*price_unit* discount/100) mienphi,
                   sum(thucthu) thucthu,
                   sum(bp0) bp0,
                   sum(bp1) bp1
            FROM (
                    SELECT pp.id product_id,pp.name_template, pu.name,pol.qty,
                    
                        pol.price_unit,pol.discount,
                        
                        case when (po.section_id = %s and pol.section_id = %s) then
                            pol.price_subtotal_incl 
                            else 0.0 end thucthu,
                    
                        case when (po.section_id = %s and pol.section_id = %s) then
                            pol.price_subtotal_incl 
                            else 0.0 end bp0,
                        
                        case when (po.section_id = %s and pol.section_id = %s) then
                            pol.price_subtotal_incl 
                            else 0.0 end bp1
                            
                    FROM pos_order_line pol inner join product_product pp on pol.product_id = pp.id
                            inner join product_template pt on pp.product_tmpl_id =pt.id
                            inner join product_uom pu on pu.id = pt.uom_id
                            inner join pos_order po on pol.order_id = po.id and po.state not in ('cancel')
                    WHERE po.date_order between '%s' and '%s')x
                group by product_id,name_template,uom_name,price_unit
                order by name_template
            '''%(self.section_id,self.section_id,
                 self.section_id,self.other_section_id[0],
                 self.section_id,self.other_section_id[1],
                 self.start_date,self.end_date)   
        self.cr.execute(sql)
        for i in self.cr.dictfetchall():
            self.total_mienphi += i['mienphi']
            self.total_thucthu +=i['thucthu']
            self.total_bp0 += i['bp0']
            self.total_bp1 += i['bp1']
            res.append(
                   {
                   'product_id':i['product_id'],
                   'name_template':i['name_template'],
                   'uom_name':i['uom_name'],
                   'price_unit':i['price_unit'] or 0.0,
                   'mienphi':i['mienphi'] or 0.0,
                   'thucthu':i['thucthu'] or 0.0,
                   'bp0':i['bp0'] or 0.0,
                   'bp1':i['bp1'] or 0.0,
                   })
        return res
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
