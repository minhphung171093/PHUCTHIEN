# -*- coding: utf-8 -*-
# #############################################################################
# 
# #############################################################################
import tools
from osv import fields, osv
from tools.translate import _
import sys
import os
import logging
_logger = logging.getLogger(__name__)

class sql_aged_partner_balance(osv.osv):
    _name = "sql.aged.partner.balance"
    _auto = False
    
    #For report
    def get_line(self, cr, start_date, account_id, partner_id, type):
        sql = '''
        select  seq, partner_code, partner_name, voucher_no, date_document,
            date_due, description, origin_amount, residual_30,
            residual_90, residual_180, residual_else, aging_day
        FROM fin_partner_aging_report ( '%s' , %s , %s, %s )
        '''%(start_date, account_id, partner_id, type)
        cr.execute(sql)
        return cr.dictfetchall()
    
    def get_total_line(self, cr, start_date, account_id, partner_id, type):
        sql = '''
        SELECT  sum(origin_amount) origin_amount,sum(residual_30) residual_30,
            sum(residual_90) residual_90, sum(residual_180) residual_180, sum(residual_else) residual_else
        FROM fin_partner_aging_report ( '%s' , %s , %s, %s )
        '''%(start_date, account_id, partner_id, type)
        
        cr.execute(sql)
        return cr.dictfetchall()
    
    def init(self, cr):
        self.fin_partner_aging_data(cr)
        self.fin_partner_aging_report(cr)
        cr.commit()
        return True
    
    def fin_partner_aging_data(self,cr):
        cr.execute("select exists (select 1 from pg_type where typname = 'fin_partner_aging_data')")
        res = cr.fetchone()
        if res and res[0]:
            cr.execute('''delete from pg_type where typname = 'fin_partner_aging_data';
                            delete from pg_class where relname='fin_partner_aging_data';
                            commit;''')
        sql = '''
        CREATE TYPE fin_partner_aging_data AS
           (seq integer,
            partner_code character varying(20),
            partner_name character varying(120),
            voucher_no character varying(64),
            date_document date,
            date_due date,
            description character varying(150),
            origin_amount numeric,
            balance_amount numeric,
            residual_30 numeric,
            residual_90 numeric,
            residual_180 numeric,
            residual_else numeric,
            aging_day integer);
        ALTER TYPE fin_partner_aging_data
          OWNER TO openerp;
        '''
        cr.execute(sql)
        return True  
    
    def fin_partner_aging_report(self,cr):
        sql = '''
        DROP FUNCTION IF EXISTS fin_partner_aging_report(date, integer, integer, boolean) CASCADE;
        commit;

        CREATE OR REPLACE FUNCTION fin_partner_aging_report(date, integer, integer, boolean)
          RETURNS SETOF fin_partner_aging_data AS
        $BODY$
        DECLARE
            rec_age        record;
            age_data    fin_partner_aging_data%ROWTYPE;
            line_no        int;
            days        int;
            type        int;
            amount        numeric;
            bal_amount    numeric;
        BEGIN
            line_no = 0;
            -- 1) query du lieu cong no va duyet qua cac dong
            for rec_age in 
                    select aih.id inv_id, avh.id pay_id, amh.date,
                        case when aih.id notnull then aih.number
                            when avh.id notnull then avh.number
                            when amh.ref isnull then aml.name
                            else amh.name end number, acc.type,
                        aml.date_maturity, rpt.ref partner_code, rpt.name partner_name,
                        aih.origin, aml.date_maturity inv_duedate, avh.date_due pay_duedate,
                        aih.name inv_desc, avh.name pay_desc, aml.debit, aml.credit,
                        aih.amount_total, aih.residual, amh.ref
                    from account_move_line aml join account_move amh on aml.move_id = amh.id
                            and amh.state = 'posted' and aml.state = 'valid'
                        join account_journal ajn on amh.journal_id = ajn.id
                            and ajn.type != 'situation'
                        join fn_get_account_child_id($2) acc on aml.account_id = acc.id
                        join res_partner rpt on aml.partner_id = rpt.id /* lien ket voi partner */
                        left join account_invoice aih on amh.id = aih.move_id /* lien ket voi invoice */
                        left join account_voucher avh on amh.id = avh.move_id /* lien ket voi payment */
                    where amh.date <= $1
                        and (aml.partner_id = $3 or $3 isnull)
                        and case when $4 = true then aml.reconcile_id notnull
                        else aml.reconcile_id isnull end
                    order by 7, 3, 4
            loop
                line_no = line_no + 1;
                
                age_data.seq = line_no;
                age_data.partner_code = rec_age.partner_code;
                age_data.partner_name = rec_age.partner_name;
                age_data.date_document = rec_age.date;
                age_data.voucher_no = rec_age.number;
                
                if rec_age.type = 'payable' then
                    amount = (rec_age.credit - rec_age.debit);
                else
                    amount = (rec_age.debit - rec_age.credit);
                end if;
                
                if rec_age.inv_id notnull then
                    days = (current_date - rec_age.inv_duedate);
                    bal_amount = rec_age.residual;
                    type = 2;
                    
                    age_data.date_due = rec_age.inv_duedate;
                    age_data.description = rec_age.inv_desc;
                elsif rec_age.pay_id notnull then
                    bal_amount = 0;
                    type = 3; days = 0;
                    
                    age_data.date_due = rec_age.pay_duedate;
                    age_data.description = rec_age.pay_desc;
                else
                    bal_amount = amount;
                    days = (current_date - rec_age.date_maturity);
                    type = 1;
                    
                    age_data.date_due = rec_age.date_maturity;
                    if rec_age.ref isnull then 
                        age_data.description = 'So du dau ky';                
                    else
                        age_data.description = rec_age.ref;
                        bal_amount = 0;     type = 4;
                    end if;
                    
                end if;
                
                age_data.balance_amount = bal_amount;
                age_data.residual_30 = 0;
                age_data.residual_90 = 0;
                age_data.residual_180 = 0;
                age_data.residual_else = 0;
                age_data.aging_day = -days;
                
                case type
                    when 1, 2 then
                        age_data.origin_amount = amount;
                        if days <= 30 then
                            age_data.residual_30 = bal_amount;
                        elsif days <= 90 then
                            age_data.residual_90 = bal_amount;
                        elsif days <= 180 then
                            age_data.residual_180 = bal_amount;
                        else
                            age_data.residual_else = bal_amount;
                        end if;
                    else
                        age_data.origin_amount = amount;
                end case;
                
                return next age_data;
            end loop;
            
            return;
        END; $BODY$
          LANGUAGE plpgsql VOLATILE
          COST 100
          ROWS 1000;
        ALTER FUNCTION fin_partner_aging_report(date, integer, integer, boolean)
          OWNER TO openerp;
        '''
        cr.execute(sql)
        return True  
    
sql_aged_partner_balance()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
