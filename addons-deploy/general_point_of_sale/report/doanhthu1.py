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
        self.total_thuletan =0.0
        self.section_id = False
        self.partner_team = []
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
            'get_total_thuletan':self.get_total_thuletan,
            
            'get_partner_team': self.get_partner_team,
        })
    
    def get_partner_team(self):
        if not len(self.partner_team):
            sql ='''
            SELECT id, name, 1::integer
            FROM res_partner
            WHERE customer_type=True
            '''
            self.cr.execute(sql)
            self.partner_team = [x for x in self.cr.fetchall()]
            
            sql ='''
            SELECT id, name, 2::integer
            FROM crm_case_section
            WHERE id <> %s
            '''%(self.section_id)
            self.cr.execute(sql)
            self.partner_team += [x for x in self.cr.fetchall()]
            
        return self.partner_team
    
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
        return self.get_vietname_date(self.start_date) 
    
    def get_end_date(self):
        return self.get_vietname_date(self.end_date) 
    
    def get_vietname_date(self, date):
        if not date:
            return ''
        date = datetime.strptime(date, DATE_FORMAT)
        return date.strftime('%d/%m/%Y')
    
    def get_vietname_datetime(self, date):
        if not date:
            return ''
        date = datetime.strptime(date, DATETIME_FORMAT)
        return date.strftime('%d/%m/%Y')
    
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
    
    def get_product_qty(self, product_id, part_or_team_id, check_type):
        if check_type == 1:
            if self.section_id:
                sql ='''
                    select sum(qty)  qty
                    FROM pos_order_line pol inner join pos_order pos on pos.id = pol.order_id and pos.partner_id = %s and pos.section_id = %s and pos.state not in ('cancel')
                    WHERE
                    pol.product_id =%s 
                    and pol.section_id is null
                    and pos.date_user_tz between '%s' and '%s'
                '''%(part_or_team_id,self.section_id,product_id,self.start_date,self.end_date)
            else:
                sql ='''
                    select sum(qty)  qty
                    FROM pos_order_line pol inner join pos_order pos on pos.id = pol.order_id and pos.partner_id = %s and pos.state not in ('cancel')
                    WHERE
                    pol.product_id =%s 
                    and pol.section_id is null
                    and pos.date_user_tz between '%s' and '%s'
                '''%(part_or_team_id,product_id,self.start_date,self.end_date)
        else:
            sql ='''
                select sum(qty)  qty
                FROM pos_order_line pol inner join pos_order pos on pos.id = pol.order_id and pos.state not in ('cancel')
                WHERE
                pol.product_id =%s 
                and pol.section_id = %s
                and pos.date_user_tz between '%s' and '%s'
            '''%(product_id,part_or_team_id,self.start_date,self.end_date)
        self.cr.execute(sql)
        for i in self.cr.dictfetchall():
            return i['qty'] or 0.0
        return 0.0
    
    def get_total_qty(self, part_or_team_id, check_type):
        if check_type == 1:
            if self.section_id:
                sql ='''
                    select sum(qty)  qty
                    FROM pos_order_line pol inner join pos_order pos on pos.id = pol.order_id and pos.partner_id = %s and pos.section_id = %s and pos.state not in ('cancel')
                    WHERE pol.section_id is null
                    and pos.date_user_tz between '%s' and '%s'
                '''%(part_or_team_id,self.section_id,self.start_date,self.end_date)
            else:
                sql ='''
                    select sum(qty)  qty
                    FROM pos_order_line pol inner join pos_order pos on pos.id = pol.order_id and pos.partner_id = %s and pos.state not in ('cancel')
                    WHERE pol.section_id is null
                    and pos.date_user_tz between '%s' and '%s'
                '''%(part_or_team_id,self.start_date,self.end_date)
        else:
            sql ='''
                select sum(qty)  qty
                FROM pos_order_line pol inner join pos_order pos on pos.id = pol.order_id and pos.state not in ('cancel')
                WHERE pol.section_id = %s
                and pos.date_user_tz between '%s' and '%s'
            '''%(part_or_team_id,self.start_date,self.end_date)
        self.cr.execute(sql)
        for i in self.cr.dictfetchall():
            return i['qty'] or 0.0
        return 0.0
    
    def get_total_mienphi(self):
        if not self.total_mienphi:
            self.get_line()
        return self.total_mienphi or 0.0
    
    def get_total_thucthu(self):
        if not self.total_thucthu:
            self.get_line()
        return self.total_thucthu or 0.0
    
    def get_total_thuletan(self):
        if not self.total_thuletan:
            self.get_line()
        return self.total_thuletan or 0.0
    
    
    def get_line(self):
        res=[]
        if not self.end_date:
            self.get_header()
        sql ='''
            SELECT product_id,name_template,name uom_name,price_unit,sum(qty*price_unit* discount/100) mienphi,
                   sum(price_subtotal_incl) thucthu,sum(amount_letan) letan
            FROM (
                    SELECT pp.id product_id,pp.name_template, pu.name,pol.qty,
                        case when pol.section_id is null then
                            pol.qty 
                            else 0.0 end qty_khach,
                        case when pol.section_id is not null then
                            pol.qty 
                            else 0.0 end qty_letan,
                            pol.price_unit,pol.discount,
                        case when pol.section_id is null then
                            pol.price_subtotal_incl 
                            else 0.0 end price_subtotal_incl,
                        case when pol.section_id is not null then
                            pol.price_subtotal_incl 
                            else 0.0 end amount_letan    
                    FROM pos_order_line pol inner join product_product pp on pol.product_id = pp.id
                            inner join product_template pt on pp.product_tmpl_id =pt.id
                            inner join product_uom pu on pu.id = pt.uom_id
                            inner join pos_order po on pol.order_id = po.id
                    WHERE timezone('UTC',po.date_order::timestamp)::date between '%s' and '%s')x
                group by product_id,name_template,uom_name,price_unit
                order by name_template
            '''%(self.start_date,self.end_date)   
        self.cr.execute(sql)
        for i in self.cr.dictfetchall():
            self.total_mienphi += i['mienphi']
            self.total_thucthu +=i['thucthu']
            self.total_thuletan +=i['letan']
            res.append(
                   {
                   'product_id':i['product_id'],
                   'name_template':i['name_template'],
                   'uom_name':i['uom_name'],
                   'price_unit':i['price_unit'] or 0.0,
                   'mienphi':i['mienphi'] or 0.0,
                   'thucthu':i['thucthu'] or 0.0,
                   'letan':i['letan'] or 0.0,
                   })
        return res
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
