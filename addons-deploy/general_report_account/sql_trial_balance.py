# -*- coding: utf-8 -*-
# #############################################################################
# 
# #############################################################################
import tools
from osv import fields, osv
from tools.translate import _

class sql_trial_balance(osv.osv):
    _name = "sql.trial.balance"
    _auto = False
    
    #For reports
    def get_total_line(self, cr, start_date, end_date, company_id):
        sql = '''
        select sum(begin_dr) begin_dr, sum(begin_cr) begin_cr,
            sum(period_dr) period_dr, sum(period_cr) period_cr, sum(end_dr) end_dr, sum(end_cr) end_cr
            from (
            SELECT  coa_code,sum(begin_dr) begin_dr, sum(begin_cr) begin_cr,
                    sum(period_dr) period_dr, sum(period_cr) period_cr, sum(end_dr) end_dr, sum(end_cr) end_cr
                FROM fin_trial_balance_report('%s', '%s', %s)
                where length(coa_code)= 3 
                and acc_level <> 10 
                and
                (
                    begin_dr notnull or begin_cr notnull
                    or period_dr notnull or period_cr notnull
                    or end_dr notnull or end_cr notnull
                )
                group by coa_code
                order by 1)x
        ''' %(start_date, end_date, company_id)
        cr.execute(sql)
        return cr.dictfetchall()    
    
    def get_total_line1(self, cr, start_date, end_date, company_id):
        
        sql = '''
        select sum(begin_dr) begin_dr, sum(begin_cr) begin_cr,
            sum(period_dr) period_dr, sum(period_cr) period_cr, sum(end_dr) end_dr, sum(end_cr) end_cr
                FROM fin_trial_balance_report('%s', '%s', %s)
                where acc_level = 10
                and (
                    begin_dr notnull or begin_cr notnull
                    or period_dr notnull or period_cr notnull
                    or end_dr notnull or end_cr notnull
                )
        ''' %(start_date, end_date, company_id)
        cr.execute(sql)
        return cr.dictfetchall()    
    
    def get_line(self, cr, start_date, end_date, company_id):
        sql = '''
        SELECT  acc_level, coa_code, coa_name, begin_dr, begin_cr,
            period_dr, period_cr, end_dr, end_cr
        FROM fin_trial_balance_report('%s', '%s', %s)
        where 
        (begin_dr notnull or begin_cr notnull
        or period_dr notnull or period_cr notnull
        or end_dr notnull or end_cr notnull)
        order by acc_level, coa_code
        ''' %(start_date, end_date, company_id)
        cr.execute(sql)
        return cr.dictfetchall()
    
    def get_line1(self, cr, start_date, end_date, company_id):
        sql = '''
        SELECT  acc_level, coa_code, coa_name, begin_dr, begin_cr,
            period_dr, period_cr, end_dr, end_cr
        FROM fin_trial_balance_report('%s', '%s', %s)
        where acc_level = 10
        and (begin_dr notnull or begin_cr notnull
        or period_dr notnull or period_cr notnull
        or end_dr notnull or end_cr notnull)
        order by acc_level, coa_code
        ''' %(start_date, end_date, company_id)
        cr.execute(sql)
        return cr.dictfetchall()
    
    def get_total_line3(self, cr, start_date, end_date, company_id):
        
        sql = '''
            select sum(begin_dr) begin_dr, sum(begin_cr) begin_cr,
                        sum(period_dr) period_dr, sum(period_cr) period_cr, sum(end_dr) end_dr, sum(end_cr) end_cr
                        from (
            select sum(begin_dr) begin_dr, sum(begin_cr) begin_cr,
                        sum(period_dr) period_dr, sum(period_cr) period_cr, sum(end_dr) end_dr, sum(end_cr) end_cr
                        from (
                        SELECT  coa_code,sum(begin_dr) begin_dr, sum(begin_cr) begin_cr,
                                sum(period_dr) period_dr, sum(period_cr) period_cr, sum(end_dr) end_dr, sum(end_cr) end_cr
                            FROM fin_trial_balance_report('%s', '%s', %s)
                            where length(coa_code)= 3 and acc_level <> 10
                            and (begin_dr notnull or begin_cr notnull
                            or period_dr notnull or period_cr notnull
                            or end_dr notnull or end_cr notnull)
                            group by coa_code
                            order by 1)x
             union
             select sum(begin_dr) begin_dr, sum(begin_cr) begin_cr,
                        sum(period_dr) period_dr, sum(period_cr) period_cr, sum(end_dr) end_dr, sum(end_cr) end_cr
                            FROM fin_trial_balance_report('%s', '%s', %s)
                            where acc_level = 10
                            and (begin_dr notnull or begin_cr notnull
                            or period_dr notnull or period_cr notnull
                            or end_dr notnull or end_cr notnull))y
        ''' %(start_date, end_date, company_id, start_date, end_date, company_id)
        cr.execute(sql)
        return cr.dictfetchall()    
    
    def init(self, cr):
        self.fin_trial_balance_data(cr)
        self.fn_trial_balance_report(cr)
        cr.commit()
        return True
    
    def fn_trial_balance_report(self,cr):
#         cr.execute("select exists (select 1 from pg_proc where proname = 'fin_trial_balance_report')")
#         res = cr.fetchone()
#         if res and res[0]:
#             return True
        sql = '''
        DROP FUNCTION IF EXISTS fin_trial_balance_report(date, date, integer) CASCADE;
        commit;
        CREATE OR REPLACE FUNCTION fin_trial_balance_report(date, date, integer)
          RETURNS SETOF fin_trial_balance_data AS
        $BODY$
        DECLARE
            rec_trial    record;
            trial_data    fin_trial_balance_data%ROWTYPE;
            line_no        int;
            begin_dr    numeric;
            begin_cr    numeric;
            end_dr        numeric;
            end_cr        numeric;
        BEGIN
            line_no = 0;
        
            for rec_trial in 
                    Select  distinct coa.acc_level, coa.code, coa.name,
                            sum(dr_beg) over w begin_dr,
                            sum(cr_beg) over w begin_cr,
                            sum(dr_period) over w period_dr,
                            sum(cr_period) over w period_cr
                    From (
                            select  case when code in ('003','000000','331009')
                                    then 10 else substr(code,1,1)::int
                                    end acc_level, code, name
                            from account_account acc where company_id = $3 and "level" > 1
                        ) coa 
                        join
                        (
                            select  code, acc_level,
                                    sum(debit) dr_beg, sum(credit) cr_beg,
                                    sum(dr_val) dr_period, sum(cr_val) cr_period
                            from (
                                /*    Lay so du dau ky    */
                                    select acc.code, case when acc.code in ('003','000000','331009')
                                                then 10 else substr(acc.code,1,1)::int
                                                    end acc_level,
                                            aml.debit,aml.credit, 0 dr_val, 0 cr_val
                                    from account_move amh join account_move_line aml 
                                            on amh.id = aml.move_id and amh.state = 'posted'
                                            and aml.state = 'valid'
                                            and date_trunc('year', aml.date) = date_trunc('year', $1::date)
                                        join account_journal ajn on amh.journal_id = ajn.id
                                            and ajn.type = 'situation'
                                        join account_account acc on aml.account_id = acc.id
                                    where amh.company_id = $3
                                    union all
                                    select acc.code, case when acc.code in ('003','000000','331009')
                                                then 10 else substr(acc.code,1,1)::int
                                                    end acc_level,
                                            sum(aml.debit), sum(aml.credit), 0, 0
                                    from account_move amh join account_move_line aml 
                                            on amh.id = aml.move_id and amh.state = 'posted'
                                            and aml.state = 'valid'
                                            and date(aml.date) between date(date_trunc('year', $1::date)) and date($1::date - 1)
                                        join account_journal ajn on amh.journal_id = ajn.id
                                            and ajn.type != 'situation'
                                        join account_account acc on aml.account_id = acc.id
                                    where amh.company_id = $3
                                    group by acc.code,case when acc.code in ('003','000000','331009')
                                            then 10 else substr(acc.code,1,1)::int end
                                    /*    Lay phat sinh trong ky    */
                                    union all
                                    select acc.code, case when acc.code in ('003','000000','331009')
                                                then 10 else substr(acc.code,1,1)::int
                                                    end acc_level,
                                            0, 0 , sum(aml.debit), sum(aml.credit)
                                    from account_move amh join account_move_line aml 
                                            on amh.id = aml.move_id and amh.state = 'posted'
                                            and aml.state = 'valid'
                                            and date(aml.date) between date($1::date) and date($2::date)
                                        join account_journal ajn on amh.journal_id = ajn.id
                                            and ajn.type != 'situation'
                                        join account_account acc on aml.account_id = acc.id
                                    where amh.company_id = $3
                                    group by acc.code,case when acc.code in ('003','000000','331009')
                                            then 10 else substr(acc.code,1,1)::int end
                                ) bal
                            group by code, acc_level
                        ) bal on bal.code like coa.code||'%' and bal.acc_level = coa.acc_level
                    Window w as (partition by coa.code)
            loop
                line_no = line_no + 1;
                begin_dr = rec_trial.begin_dr - rec_trial.begin_cr;
                if begin_dr >= 0 then
                    begin_cr = 0;
                else
                    begin_cr = -begin_dr;
                    begin_dr = 0;
                end if;
                end_dr = begin_dr + rec_trial.period_dr - begin_cr - rec_trial.period_cr;
                if end_dr >= 0 then
                    end_cr = 0;
                else
                    end_cr = -end_dr;
                    end_dr = 0;
                end if;
            
                trial_data.seq = line_no;
                trial_data.coa_code = rec_trial.code;
                trial_data.coa_name = rec_trial.name;
                trial_data.begin_dr = nullif(begin_dr,0);
                trial_data.begin_cr = nullif(begin_cr,0);
                trial_data.period_dr = nullif(rec_trial.period_dr,0);
                trial_data.period_cr = nullif(rec_trial.period_cr,0);
                trial_data.end_dr = nullif(end_dr,0);
                trial_data.end_cr = nullif(end_cr,0);
                trial_data.acc_level = rec_trial.acc_level;
                
                return next trial_data;
            end loop;
            
            return;
        END; $BODY$
          LANGUAGE plpgsql VOLATILE
          COST 100
          ROWS 1000;
        ALTER FUNCTION fin_trial_balance_report(date, date, integer)
          OWNER TO openerp;
        '''
        cr.execute(sql)
        return True  
    
    def fin_trial_balance_data(self,cr):
        cr.execute("select exists (select 1 from pg_type where typname = 'fin_trial_balance_data')")
        res = cr.fetchone()
        if res and res[0]:
            cr.execute('''delete from pg_type where typname = 'fin_trial_balance_data';
                            delete from pg_class where relname='fin_trial_balance_data';
                            commit;''')
        sql = '''
        CREATE TYPE fin_trial_balance_data AS
           (seq integer,
            coa_code character varying(20),
            coa_name character varying(120),
            begin_dr numeric,
            begin_cr numeric,
            period_dr numeric,
            period_cr numeric,
            end_dr numeric,
            end_cr numeric,
            acc_level integer);
        ALTER TYPE fin_trial_balance_data
          OWNER TO openerp;
        '''
        cr.execute(sql)
        return True  

sql_trial_balance()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
