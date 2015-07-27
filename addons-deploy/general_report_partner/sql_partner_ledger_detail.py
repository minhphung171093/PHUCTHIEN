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

class sql_partner_ledger_detail(osv.osv):
    _name = "sql.partner.ledger.detail"
    _auto = False
    
    #For reports
    def get_total_line(self, cr, start_date, end_date, account_id):
        sql ='''
            select sum(begin_dr) begin_dr,sum(begin_cr) begin_cr,sum(period_dr) period_dr,
            sum(period_cr) period_cr,sum(end_dr) end_dr,sum(end_cr) end_cr 
            from fin_gen_liability_data('%s','%s',%s);
        '''%(start_date, end_date, account_id)
        cr.execute(sql)
        
        cr.execute(sql)
        return cr.dictfetchall()
    
    def get_line(self, cr, start_date, end_date, account_id):
        sql ='''
            select* from fin_gen_liability_data('%s','%s',%s);
        '''%(start_date, end_date, account_id)
        cr.execute(sql)
        return cr.dictfetchall()
    
    def init(self, cr):
        self.fin_gen_liability_data(cr)
        self.fin_liability_data(cr)
        cr.commit()
        return True
    
    def fin_gen_liability_data(self,cr):
        cr.execute("select exists (select 1 from pg_type where typname = 'fin_gen_liability_data')")
        res = cr.fetchone()
        if res and res[0]:
            cr.execute('''delete from pg_type where typname = 'fin_gen_liability_data';
                            delete from pg_class where relname='fin_gen_liability_data';
                            commit;''')
        sql = '''
        CREATE TYPE fin_gen_liability_data AS
           (seq integer,
            partner_code character varying(20),
            partner_name character varying(120),
            begin_dr numeric,
            begin_cr numeric,
            period_dr numeric,
            period_cr numeric,
            end_dr numeric,
            end_cr numeric);
        ALTER TYPE fin_gen_liability_data
          OWNER TO openerp;
        '''
        cr.execute(sql)
        return True  
    
    def fin_liability_data(self,cr):
        sql = '''
        DROP FUNCTION IF EXISTS fin_gen_liability_data(date, date, integer) CASCADE;
        commit;
        
        CREATE OR REPLACE FUNCTION fin_gen_liability_data(date, date, integer)
          RETURNS SETOF fin_gen_liability_data AS
        $BODY$
        DECLARE
            rec_data    record;
            lia_data    fin_gen_liability_data%ROWTYPE;
            line_no        int;
            beg_amount    numeric;
            end_amount    numeric;
        BEGIN
            line_no = 0;
        
            for rec_data in
                    select  partner_code, partner_name,
                            sum(beg_dr) begin_dr, sum(beg_cr) begin_cr,
                            sum(prd_dr) period_dr, sum(prd_cr) period_cr
                    from (
                            /*    Lay so du dau ky    */
                            select rpt.ref as partner_code, rpt.name as partner_name,
                                    sum(aml.debit) as beg_dr, sum(aml.credit) as beg_cr, 
                                    0 as prd_dr, 0 as prd_cr
                            from account_move amh join account_move_line aml on amh.id = aml.move_id
                                    and amh.state = 'posted' and aml.state = 'valid'
                                join account_journal ajn on amh.journal_id = ajn.id
                                    and ajn.type = 'situation'
                                join fn_get_account_child_id($3) acc on aml.account_id = acc.id
                                join res_partner rpt on aml.partner_id = rpt.id /* lien ket voi partner */
                            where date_trunc('year', aml.date) = date_trunc('year', $1::date)
                            group by rpt.ref, rpt.name
                        union all
                            select  rpt.ref as partner_code, rpt.name as partner_name,
                                    sum(aml.debit) as beg_dr, sum(aml.credit) as beg_cr, 
                                    0 as prd_dr, 0 as prd_cr
                            from account_move_line aml join account_move amh on aml.move_id = amh.id
                                    and amh.state = 'posted' and aml.state = 'valid'
                                join account_journal ajn on amh.journal_id = ajn.id
                                    and ajn.type != 'situation'
                                join fn_get_account_child_id($3) acc on aml.account_id = acc.id
                                join res_partner rpt on aml.partner_id = rpt.id /* lien ket voi partner */
                            where aml.date >= date(date_trunc('year', $1::date)) and aml.date < $1
                            group by rpt.ref, rpt.name
                        union all
                            /*    Lay phat sinh trong ky    */
                            select  rpt.ref as partner_code, rpt.name as partner_name,
                                    0 as beg_dr, 0 as beg_cr,
                                    sum(aml.debit) as prd_dr, sum(aml.credit) as prd_cr
                            from account_move_line aml join account_move amh on aml.move_id = amh.id
                                    and amh.state = 'posted' and aml.state = 'valid'
                                join account_journal ajn on amh.journal_id = ajn.id
                                    and ajn.type != 'situation'
                                join fn_get_account_child_id($3) acc on aml.account_id = acc.id
                                join res_partner rpt on aml.partner_id = rpt.id /* lien ket voi partner */
                            where aml.date between $1 and $2
                            group by rpt.ref, rpt.name
                        ) vw
                    group by partner_code, partner_name
                    having sum(beg_dr) <> sum(beg_cr) or
                        sum(prd_dr) <> 0 or sum(prd_cr) <> 0
                    order by 1
            loop
                line_no = line_no + 1;
                beg_amount = rec_data.begin_dr - rec_data.begin_cr;
                end_amount = beg_amount + rec_data.period_dr - rec_data.period_cr;
            
                lia_data.seq = line_no;
                lia_data.partner_code = rec_data.partner_code;
                lia_data.partner_name = rec_data.partner_name;
                if beg_amount >= 0 then
                    lia_data.begin_dr = beg_amount;
                    lia_data.begin_cr = 0;
                else
                    lia_data.begin_dr = 0;
                    lia_data.begin_cr = -beg_amount;
                end if;
                lia_data.period_dr = rec_data.period_dr;
                lia_data.period_cr = rec_data.period_cr;
                if end_amount >= 0 then
                    lia_data.end_dr = end_amount;
                    lia_data.end_cr = 0;
                else
                    lia_data.end_dr = 0;
                    lia_data.end_cr = -end_amount;
                end if;
                
                return next lia_data;
            end loop;
            
            return;
        END; $BODY$
          LANGUAGE plpgsql VOLATILE
          COST 100
          ROWS 1000;
        ALTER FUNCTION fin_gen_liability_data(date, date, integer)
          OWNER TO openerp;
        '''
        cr.execute(sql)
        return True  
    
sql_partner_ledger_detail()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
