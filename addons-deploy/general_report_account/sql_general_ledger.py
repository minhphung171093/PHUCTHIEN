# -*- coding: utf-8 -*-
# #############################################################################
# 
# #############################################################################
import tools
from osv import fields, osv
from tools.translate import _

class sql_general_ledger(osv.osv):
    _name = "sql.general.ledger"
    _auto = False
    
    def get_line(self, cr, start_date, end_date, company_id, shop_ids):
        sql = '''
        SELECT  coa_code, coa_name, format,
            nullif(begin_dr, 0) begin_dr, nullif(begin_cr, 0) begin_cr,
            nullif(period_dr, 0) period_dr, nullif(period_cr, 0) period_cr,
            nullif(end_dr, 0) end_dr, nullif(end_cr, 0) end_cr
        FROM fin_general_ledger_report('%s', '%s', %s, ARRAY%s::int[])
        WHERE  begin_dr <>0 or begin_cr <>0
                or period_dr <>0 or period_cr <>0
                or end_dr <>0 or end_cr <>0
        ORDER BY acc_level, coa_code;
        ''' %(start_date,end_date, company_id, shop_ids)
        cr.execute(sql)
        return cr.dictfetchall()
    
    def init(self, cr):
        self.fin_general_ledger_data(cr)
        self.fin_general_ledger_report(cr)
        cr.commit()
        return True
    
    def fin_general_ledger_report(self,cr):
#         cr.execute("select exists (select 1 from pg_proc where proname = 'fin_trial_balance_report')")
#         res = cr.fetchone()
#         if res and res[0]:
#             return True
        sql = '''
        DROP FUNCTION IF EXISTS fin_general_ledger_report(date, date, integer, int[]) CASCADE;
        commit;
        CREATE OR REPLACE FUNCTION fin_general_ledger_report(date, date, integer, int[])
          RETURNS SETOF fin_gen_ledger_data AS
        $BODY$
        DECLARE
            rec_data    record;
            ledger_data    fin_gen_ledger_data%ROWTYPE;
            prev_date    date;
        BEGIN
            prev_date = date($1) - 1;
            
            for rec_data in
                    Select  distinct coa.acc_level, coa.code, coa.name, format,
                            sum(begin_dr) over w begin_dr,
                            sum(begin_cr) over w begin_cr,
                            sum(period_dr) over w period_dr,
                            sum(period_cr) over w period_cr,
                            sum(end_dr) over w end_dr,
                            sum(end_cr) over w end_cr
                    From (
                            select  case when acc_parent.code in ('X10')
                                    then 10 else substr(acc.code,1,1)::int
                                    end acc_level, acc.code, acc.name,
                                    case when acc.type = 'view' or length(acc.code) = 3
                                    then 1 else 0 end format
                            from account_account acc
                                join account_account acc_parent on acc.parent_id = acc_parent.id
                            where acc.level > 1
                        ) coa join
                        (
                            select  code, acc_level,
                                    case when type in ('payable', 'receivable') then
                                        sum(begin_dr) else
                                    case when sum(begin_dr) > sum(begin_cr) then
                                        sum(begin_dr) - sum(begin_cr) else 0 end end begin_dr,
                                    case when type in ('payable', 'receivable') then
                                        sum(begin_cr) else
                                    case when sum(begin_cr) > sum(begin_dr) then
                                        sum(begin_cr) - sum(begin_dr) else 0 end end begin_cr,
                                    sum(period_dr) period_dr, sum(period_cr) period_cr,
                                    case when type in ('payable', 'receivable') then
                                        sum(end_dr) else
                                    case when sum(end_dr) > sum(end_cr) then
                                        sum(end_dr) - sum(end_cr) else 0 end end end_dr,
                                    case when type in ('payable', 'receivable') then
                                        sum(end_cr) else
                                    case when sum(end_cr) > sum(end_dr) then
                                        sum(end_cr) - sum(end_dr) else 0 end end end_cr
                            from (
                                    /*    Lay so du dau ky    */
                                    select  code, acc_level, type, partner_id,
                                            case when sum(debit) > sum(credit) then
                                            sum(debit) - sum(credit) else 0 end begin_dr,
                                            case when sum(debit) < sum(credit) then
                                            sum(credit) - sum(debit) else 0 end begin_cr,
                                            0 period_dr, 0 period_cr, 0 end_dr, 0 end_cr
                                    from (
                                            select acc.code, case when acc_parent.code in ('X10')
                                                    then 10 else substr(acc.code,1,1)::int
                                                        end acc_level, acc.type, aml.partner_id,
                                                    aml.debit,aml.credit
                                            from account_move amh join account_move_line aml on amh.id = aml.move_id
                                                    and amh.shop_id = any($4)
                                                    and amh.company_id=$3
                                                    and amh.state = 'posted' and aml.state = 'valid'
                                                    and date_trunc('year', aml.date) = date_trunc('year', prev_date)
                                                join account_journal ajn on amh.journal_id = ajn.id and ajn.type = 'situation'
                                                join account_account acc on aml.account_id = acc.id
                                                join account_account acc_parent on acc.parent_id = acc_parent.id
                                            union all
                                            select acc.code, case when acc_parent.code in ('X10')
                                                    then 10 else substr(acc.code,1,1)::int
                                                        end acc_level, acc.type, aml.partner_id,
                                                    sum(aml.debit), sum(aml.credit)
                                            from account_move amh join account_move_line aml on amh.id = aml.move_id
                                                    and amh.shop_id = any($4)
                                                    and amh.company_id=$3
                                                    and amh.state = 'posted' and aml.state = 'valid'
                                                    and date(aml.date) between date_trunc('year', prev_date) and date(prev_date)
                                                join account_journal ajn on amh.journal_id = ajn.id and ajn.type != 'situation'
                                                join account_account acc on aml.account_id = acc.id
                                                join account_account acc_parent on acc.parent_id = acc_parent.id
                                            group by acc.code, acc.type, aml.partner_id,
                                                     case when acc_parent.code in ('X10')
                                                     then 10 else substr(acc.code,1,1)::int end
                                        ) beg_balance
                                    group by code, acc_level, type, partner_id
                                    /*    Lay phat sinh trong ky    */
                                    union all
                                    select acc.code, case when acc_parent.code in ('X10')
                                            then 10 else substr(acc.code,1,1)::int
                                                end acc_level, acc.type, aml.partner_id,
                                            0, 0, sum(aml.debit), sum(aml.credit), 0, 0
                                    from account_move amh join account_move_line aml on amh.id = aml.move_id
                                            and amh.shop_id = any($4)
                                            and amh.company_id=$3
                                            and amh.state = 'posted' and aml.state = 'valid'
                                            and date(aml.date) between date($1) and date($2)
                                        join account_journal ajn on amh.journal_id = ajn.id and ajn.type != 'situation'
                                        join account_account acc on aml.account_id = acc.id
                                        join account_account acc_parent on acc.parent_id = acc_parent.id
                                    group by acc.code, acc.type, aml.partner_id,
                                             case when acc_parent.code in ('X10')
                                             then 10 else substr(acc.code,1,1)::int end
                                    union all
                                    /*    Lay so du cuoi ky    */
                                    select  code, acc_level, type, partner_id,
                                            0, 0, 0, 0,
                                            case when sum(debit) > sum(credit) then
                                            sum(debit) - sum(credit) else 0 end,
                                            case when sum(debit) < sum(credit) then
                                            sum(credit) - sum(debit) else 0 end
                                    from (
                                            select acc.code, case when acc_parent.code in ('X10')
                                                    then 10 else substr(acc.code,1,1)::int
                                                        end acc_level, acc.type, aml.partner_id,
                                                    aml.debit,aml.credit
                                            from account_move amh join account_move_line aml on amh.id = aml.move_id
                                                    and amh.shop_id = any($4)
                                                    and amh.company_id=$3
                                                    and amh.state = 'posted' and aml.state = 'valid'
                                                    and date_trunc('year', aml.date) = date_trunc('year', $2)
                                                join account_journal ajn on amh.journal_id = ajn.id and ajn.type = 'situation'
                                                join account_account acc on aml.account_id = acc.id
                                                join account_account acc_parent on acc.parent_id = acc_parent.id
                                            union all
                                            select acc.code, case when acc_parent.code in ('X10')
                                                    then 10 else substr(acc.code,1,1)::int
                                                        end acc_level, acc.type, aml.partner_id,
                                                    sum(aml.debit), sum(aml.credit)
                                            from account_move amh join account_move_line aml on amh.id = aml.move_id
                                                    and amh.shop_id = any($4)
                                                    and amh.company_id=$3
                                                    and amh.state = 'posted' and aml.state = 'valid'
                                                    and date(aml.date) between date_trunc('year', $2) and date($2)
                                                join account_journal ajn on amh.journal_id = ajn.id and ajn.type != 'situation'
                                                join account_account acc on aml.account_id = acc.id
                                                join account_account acc_parent on acc.parent_id = acc_parent.id
                                            group by acc.code, acc.type, aml.partner_id,
                                                     case when acc_parent.code in ('X10')
                                                     then 10 else substr(acc.code,1,1)::int end
                                        ) end_balance
                                    group by code, acc_level, type, partner_id
                                ) data
                            group by code, acc_level, type
                        ) report on report.code like coa.code||'%' and report.acc_level = coa.acc_level
                    Window w as (partition by coa.code)
            loop
                ledger_data.format = rec_data.format;
                ledger_data.acc_level = rec_data.acc_level;
                ledger_data.coa_code = rec_data.code;
                ledger_data.coa_name = rec_data.name;
                ledger_data.begin_dr = rec_data.begin_dr;
                ledger_data.begin_cr = rec_data.begin_cr;
                ledger_data.period_dr = rec_data.period_dr;
                ledger_data.period_cr = rec_data.period_cr;
                ledger_data.end_dr = rec_data.end_dr;
                ledger_data.end_cr = rec_data.end_cr;
                
                return next ledger_data;
            end loop;
            
            return;
        END; $BODY$
          LANGUAGE plpgsql VOLATILE
          COST 100
          ROWS 1000;
        ALTER FUNCTION fin_general_ledger_report(date, date, integer, int[])
          OWNER TO openerp;
        '''
        cr.execute(sql)
        return True
    
    def fin_general_ledger_data(self,cr):
        cr.execute("select exists (select 1 from pg_type where typname = 'fin_gen_ledger_data')")
        res = cr.fetchone()
        if res and res[0]:
            cr.execute('''delete from pg_type where typname = 'fin_gen_ledger_data';
                            delete from pg_class where relname='fin_gen_ledger_data';
                            commit;''')
        sql = '''
        CREATE TYPE fin_gen_ledger_data AS
           (acc_level integer,
            coa_code character varying(20),
            coa_name character varying(120),
            begin_dr numeric,
            begin_cr numeric,
            period_dr numeric,
            period_cr numeric,
            end_dr numeric,
            end_cr numeric,
            format integer);
        ALTER TYPE fin_gen_ledger_data
          OWNER TO openerp;
        '''
        cr.execute(sql)
        return True  

sql_general_ledger()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
