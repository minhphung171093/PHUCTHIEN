# -*- coding: utf-8 -*-
# #############################################################################
# 
# #############################################################################
import tools
from osv import fields, osv
from tools.translate import _
import openerp.tools as tools
import decimal_precision as dp
import openerp.modules
import sys
import os
import logging
_logger = logging.getLogger(__name__)

class sql_account_in_out_tax(osv.osv):
    _name = "sql.account.in.out.tax"
    _auto = False
    
    #For reports
    def get_line_type_out(self, cr, start_date, end_date, company_id):
        sql = '''
            select distinct line_type from fin_vatout_report('%s', '%s', %s) order by line_type
        '''%(start_date, end_date, company_id)
        cr.execute(sql)
        return cr.dictfetchall()
    
    def get_line_total_out(self, cr, start_date, end_date, company_id, line_type):
        sql ='''
            select sum(base_amount) amount_total,sum(tax_amount) amount_tax from fin_vatout_report('%s', '%s', %s) where line_type = %s
             '''%(start_date, end_date, company_id, line_type)
        cr.execute(sql)
        return cr.dictfetchall();
    
    def get_line_out(self, cr, start_date, end_date, company_id, line_type):
        sql ='''
            select* from fin_vatout_report('%s', '%s', %s) where line_type = %s
             '''%(start_date, end_date, company_id, line_type)
        cr.execute(sql)
        return cr.dictfetchall()
    
    def get_line_type_in(self, cr, start_date, end_date, company_id):
        sql = '''
            select distinct line_type from fin_vatin_report('%s', '%s', %s) order by line_type
        '''%(start_date, end_date, company_id)
        cr.execute(sql)
        return cr.dictfetchall()
    
    def get_line_total_in(self, cr, start_date, end_date, company_id, line_type):
        sql ='''
            select sum(base_amount) amount_total,sum(tax_amount) amount_tax from fin_vatin_report('%s', '%s', %s) where line_type = %s
             '''%(start_date, end_date, company_id, line_type)
        cr.execute(sql)
        return cr.dictfetchall();
    
    def get_line_in(self, cr, start_date, end_date, company_id, line_type):
        sql ='''
            select * from fin_vatin_report('%s', '%s', %s) where line_type = %s
             '''%(start_date, end_date, company_id, line_type)
        cr.execute(sql)
        return cr.dictfetchall()
    
    def init(self, cr):
        self.fin_vat_data(cr)
        self.fin_vatin_report(cr)
        self.fin_vatout_report(cr)
        cr.commit()
        return True
    
    def fin_vat_data(self,cr):
        cr.execute("select exists (select 1 from pg_type where typname = 'fin_vat_data')")
        res = cr.fetchone()
        if res and res[0]:
            cr.execute('''delete from pg_type where typname = 'fin_vat_data';
                            delete from pg_class where relname='fin_vat_data';
                            commit;''')
        sql = '''
        CREATE TYPE fin_vat_data AS
           (seq integer,
            regcode character varying(64),
            registry character varying(64),
            reference character varying(64),
            "number" character varying(64),
            date_document date,
            date_gl date,
            supplier_name character varying(128),
            tax_code character varying(32),
            description character varying(100),
            vat character varying(10),
            base_amount numeric,
            tax_amount numeric,
            notes character varying(100),
            line_type integer);
        ALTER TYPE fin_vat_data
          OWNER TO openerp;
        '''
        cr.execute(sql)
        return True
    
    def fin_vatout_report(self,cr):
#         cr.execute("select exists (select 1 from pg_proc where proname = 'fin_vatout_report')")
#         res = cr.fetchone()
#         if res and res[0]:
#             return True
        sql = '''
        DROP FUNCTION IF EXISTS fin_vatout_report(date, date, integer) CASCADE;
        commit;
        
        CREATE OR REPLACE FUNCTION fin_vatout_report(date, date, integer)
          RETURNS SETOF fin_vat_data AS
        $BODY$
        DECLARE
            rec            record;
            rec_tax        record;
            tax_data    fin_vat_data%ROWTYPE;
            line_no        int;
            type        int = 1;
            num_sign    int;
            registry    varchar(64);
        BEGIN
            select company_registry into registry from res_company limit 1;
            -- 1) add type loai 1
                tax_data.seq = 1;
                tax_data.registry = null;
                tax_data.reference = null;
                tax_data.number = null;
                tax_data.date_document = null;
                tax_data.date_gl = null;
                tax_data.supplier_name = null;
                tax_data.tax_code = null;
                tax_data.description = null;
                tax_data.vat = null;
                tax_data.base_amount = null;
                tax_data.tax_amount = null;
                tax_data.line_type = type;
                tax_data.notes = null;
                
            return next tax_data;
        
            -- 2) query thue vat out va duyet qua cac dong du lieu theo tung loai thue
            for rec in select* from account_tax tax where tax.type_tax_use = 'sale' order by sequence
            loop
                line_no = 0;
                type = type + 1;
                for rec_tax in
                        select aih.reference, aih.number, amh.date date_document, amh.date,
                            rpt.name supplier_name, rpt.vat tax_code, aih.name description,
                            (tax.amount*100)::int::text vat,
                            aih.amount_untaxed, aih.amount_tax,
                            ait.base::numeric base_amount, ait.amount tax_amount,
                            aih.type, (select count(*) from account_invoice_tax ait2
                                    where ait2.invoice_id = aih.id) tax_count
                        from account_invoice_tax ait join account_invoice aih
                                on ait.invoice_id = aih.id
                            join account_move amh on aih.move_id = amh.id
                            join res_partner rpt on aih.partner_id = rpt.id
                            join account_tax_code atc on ait.tax_code_id = atc.id
                            join account_tax tax on tax.tax_code_id = atc.id
                        where ait.company_id = $3 and aih.type <> 'in_invoice' and amh.state = 'posted'
                            and date(amh.date) between $1 and $2
                            and tax.amount = rec.amount
                        union all
                        select avh.reference, avh.number, avh.date date_document, avh.date,
                            rpt.name supplier_name, rpt.vat tax_code, avh.name description,
                            (tax.amount*100)::int::text vat,
                            (avh.amount - avh.tax_amount)::numeric untax_amount, avh.tax_amount,
                            null, null, 'direct_pay', 1
                        from account_voucher avh
                            join account_move amh on avh.move_id = amh.id
                            join res_partner rpt on avh.partner_id = rpt.id
                            join account_tax tax on avh.tax_id = tax.id
                        where avh.state = 'posted' and avh.company_id = $3 and avh.tax_id notnull and amh.state = 'posted'
                            and date(amh.date) between $1 and $2
                            and tax.type_tax_use='sale'
                            and tax.amount = rec.amount
                        order by 3, 2
                loop
                    line_no = line_no + 1;
                    if (rec_tax.type = 'out_refund') then
                        num_sign = -1;
                    else
                        num_sign = 1;
                    end if;
                    
                    tax_data.seq = line_no;
                    tax_data.registry = registry;
                    tax_data.reference = rec_tax.reference;
                    tax_data.number = rec_tax.number;
                    tax_data.date_document = rec_tax.date_document;
                    tax_data.date_gl = rec_tax.date;
                    tax_data.supplier_name = rec_tax.supplier_name;
                    tax_data.tax_code = rec_tax.tax_code;
                    tax_data.description = rec_tax.description;
                    tax_data.vat = rec_tax.vat;
                    if rec_tax.tax_count = 1 then
                        tax_data.base_amount = num_sign*rec_tax.amount_untaxed;
                        tax_data.tax_amount = num_sign*rec_tax.amount_tax;
                    else
                        tax_data.base_amount = num_sign*rec_tax.base_amount;
                        tax_data.tax_amount = num_sign*rec_tax.tax_amount;
                    end if;
                    tax_data.line_type = type;
                    tax_data.notes = null;
                    
                    return next tax_data;
                end loop;
                -- neu truy van theo dong thue khong co du lieu
                -- => add them 1 dong trong vao dong thue do
                if line_no = 0 then
                    tax_data.seq = 1;
                    tax_data.registry = null;
                    tax_data.reference = null;
                    tax_data.number = null;
                    tax_data.date_document = null;
                    tax_data.date_gl = null;
                    tax_data.supplier_name = null;
                    tax_data.tax_code = null;
                    tax_data.description = null;
                    tax_data.vat = null;
                    tax_data.base_amount = null;
                    tax_data.tax_amount = null;
                    tax_data.line_type = type;
                    tax_data.notes = null;
                    
                    return next tax_data;
                end if;
            end loop;
            -- query cac invoice khong thue va add vao loai 5
            -- 3) add type loai 5
            type = type + 1;
                tax_data.seq = 1;
                tax_data.registry = null;
                tax_data.reference = null;
                tax_data.number = null;
                tax_data.date_document = null;
                tax_data.date_gl = null;
                tax_data.supplier_name = null;
                tax_data.tax_code = null;
                tax_data.description = null;
                tax_data.vat = null;
                tax_data.base_amount = null;
                tax_data.tax_amount = null;
                tax_data.line_type = type;
                tax_data.notes = null;
                
            return next tax_data;
            
            return;
        END; $BODY$
          LANGUAGE plpgsql VOLATILE
          COST 100
          ROWS 1000;
        ALTER FUNCTION fin_vatout_report(date, date, integer)
          OWNER TO openerp;
        '''
        cr.execute(sql)
        return True
    
    def fin_vatin_report(self,cr):
        sql = '''
        DROP FUNCTION IF EXISTS fin_vatin_report(date, date, integer) CASCADE;
        commit;
        
        CREATE OR REPLACE FUNCTION fin_vatin_report(date, date, integer)
          RETURNS SETOF fin_vat_data AS
        $BODY$
        DECLARE
            rec_tax            record;
            tax_data        fin_vat_data%ROWTYPE;
            line_no            int;
            type            int;
        BEGIN
            -- 1) query thue vat in va duyet qua cac dong du lieu
            line_no = 0;
            -- add type loai 1
            for rec_tax in
                    select rpt.website registry, aih.reference, aih.number, amh.date date_document,
                        amh.date, rpt.name supplier_name, rpt.vat tax_code, aih.name description,
                        (tax.amount*100)::int::text vat,
                        aih.amount_untaxed, aih.amount_tax,
                        ait.base::numeric base_amount, ait.amount tax_amount,
                        aih.type, (select count(*) from account_invoice_tax ait2
                                where ait2.invoice_id = aih.id) tax_count
                    from account_invoice_tax ait join account_invoice aih
                            on ait.invoice_id = aih.id
                        join account_move amh on aih.move_id = amh.id
                        join res_partner rpt on aih.partner_id = rpt.id
                        join account_tax_code atc on ait.tax_code_id = atc.id
                        join account_tax tax on tax.tax_code_id = atc.id
                    where aih.company_id = $3 and aih.type = 'in_invoice' and amh.state = 'posted'
                        and date(amh.date) between $1 and $2
                    union all
                    select rpt.website registry, avh.reference, avh.number, avh.date date_document,
                        avh.date, rpt.name supplier_name, rpt.vat tax_code, avh.name description,
                        (tax.amount*100)::int::text vat,
                        (avh.amount - avh.tax_amount)::numeric untax_amount, avh.tax_amount,
                        null, null, 'direct_pay', 1
                    from account_voucher avh 
                        join account_move amh on avh.move_id = amh.id
                        join res_partner rpt on avh.partner_id = rpt.id
                        join account_tax tax on avh.tax_id = tax.id
                    where avh.state = 'posted' and avh.company_id = $3 and avh.tax_id notnull and amh.state = 'posted'
                        and date(amh.date) between $1 and $2
                        and tax.type_tax_use='purchase'
                    order by 3, 5, 2
            loop
                line_no = line_no + 1;
                
                tax_data.seq = line_no;
                tax_data.registry = rec_tax.registry;
                tax_data.reference = rec_tax.reference;
                tax_data.number = rec_tax.number;
                tax_data.date_document = rec_tax.date_document;
                tax_data.date_gl = rec_tax.date;
                tax_data.supplier_name = rec_tax.supplier_name;
                tax_data.tax_code = rec_tax.tax_code;
                tax_data.description = rec_tax.description;
                tax_data.vat = rec_tax.vat;
                
                if rec_tax.tax_count = 1 then
                    tax_data.base_amount = rec_tax.amount_untaxed;
                    tax_data.tax_amount = rec_tax.amount_tax;
                else
                    tax_data.base_amount = rec_tax.base_amount;
                    tax_data.tax_amount = rec_tax.tax_amount;
                end if;
                
                tax_data.line_type = 1;
                if (rec_tax.base_amount+rec_tax.tax_amount) >= 20000000 then
                    tax_data.notes = 'X';
                else
                    tax_data.notes = null;
                end if;
                
                return next tax_data;
            end loop;
            
            -- add type loai 2 -> 5
            for type in 2..5 loop
                tax_data.seq = 1;
                tax_data.registry = null;
                tax_data.reference = null;
                tax_data.number = null;
                tax_data.date_document = null;
                tax_data.date_gl = null;
                tax_data.supplier_name = null;
                tax_data.tax_code = null;
                tax_data.description = null;
                tax_data.vat = null;
                tax_data.base_amount = null;
                tax_data.tax_amount = null;
                tax_data.line_type = type;
                tax_data.notes = null;
                return next tax_data;    
            end loop;
            
            return;
        END; $BODY$
          LANGUAGE plpgsql VOLATILE
          COST 100
          ROWS 1000;
        ALTER FUNCTION fin_vatin_report(date, date, integer)
          OWNER TO openerp;
        '''
        cr.execute(sql)
        return True

sql_account_in_out_tax()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
