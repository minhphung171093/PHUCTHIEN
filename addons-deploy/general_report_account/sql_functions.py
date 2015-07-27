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

class sql_function(osv.osv):
    _name = "sql.function"
    _auto = False
    
    def init(self, cr):
        #Create Type
        self.finance_data(cr)
        self.fn_get_prior_rangedate(cr)
        self.fin_get_array_accountid(cr)
        self.fin_get_array_accountid2(cr)
        self.fn_get_account_child_id(cr)
        
        #Create SQL Report Cash Bank Book
#         self.fn_cashbank_book_type(cr)
#         self.fn_cashbank_begin(cr)
#         self.fn_cashbank_end(cr)
#         self.fn_cashbank_book_report(cr)
        
        cr.commit()
#        try:
#            cr.execute("""
#                CREATE LANGUAGE 'plpythonu'
#                """)
#            cr.commit()
#        except:
#            pass
        
        # Execute SQL FIle
#        sql_files = [
#                     'vinhthai_base/sql/func.lookupquery 2.sql',
#                     ]
#        for sql_file in sql_files:
#            path = os.path.abspath('../addons/' + str(sql_file))
#            f = open(path, "r")
#            try:
#                sql_file = f.read()
#                queries = (sql_file.split(';;'))
#                for query in queries:
#                    if query.strip():
#                        try:
#                            cr.execute(query)
#                        except:
#                            _logger.debug ('ERROR OCCURED: ' + str(sys.exc_info()[1]))
#                f.close()
#            except:
#                pass
#            finally:
#                f.close()
#        module = 'vinhthai_base'
#        try:
#            self.run_sql(cr, module, 'sql/func.lookupquery 2.sql')
#        except:
#            pass
        return True
    
    def fin_get_array_accountid2(self, cr):
        sql = '''
        DROP FUNCTION IF EXISTS fin_get_array_accountid2(text, text) CASCADE;
        commit;
        
        CREATE OR REPLACE FUNCTION fin_get_array_accountid2(text, text)
          RETURNS text AS
        $BODY$
        DECLARE
            rec        record;
            rec2    record;
            acc_except    text;
            result    text = '';
            sql    text = '';
            where_except    text = '';
        BEGIN
            acc_except = fin_get_array_accountid($2);
            if acc_except <> '' then
                where_except = ' and aaa.id not in ('||acc_except||')';
            end if;
            for rec in select regexp_split_to_table($1, ' ') as acc_code
            loop
                sql = 'select id from account_account aaa where aaa.code ~~ ''' + " '''||rec.acc_code||'%'' " + '''
                        and type <> ''view'' '||where_except||' order by code';
                for rec2 in execute sql
                loop
                    result = result||rec2.id::text||',';
                end loop;
            end loop;
            
            if length(result) = 0 then
                return result;
            else
                return substr(result,1,length(result) - 1);
            end if;
        END;$BODY$
          LANGUAGE plpgsql VOLATILE
          COST 100;
        ALTER FUNCTION fin_get_array_accountid2(text, text)
          OWNER TO openerp;
        '''
        cr.execute(sql)
        return True
    
    def fin_get_array_accountid(self, cr):
#         cr.execute("select exists (select 1 from pg_type where typname = 'fin_get_array_accountid')")
#         res = cr.fetchone()
#         if res and res[0]:
#             return True
        sql = '''
        DROP FUNCTION IF EXISTS fin_get_array_accountid(text) CASCADE;
        commit;
        
        CREATE OR REPLACE FUNCTION fin_get_array_accountid(text)
          RETURNS text AS
        $BODY$
        DECLARE
            rec        record;
            rec2    record;
            result    text = '';
        BEGIN
            
            for rec in select regexp_split_to_table($1, ' ') as acc_code
            loop
                for rec2 in execute 'select id from account_account aaa where aaa.code ~~ '''+ " '''||rec.acc_code||'%'' " +''' and type <> ''view'' order by code'
                loop
                    result = result||rec2.id::text||',';
                end loop;
            end loop;
            
            if length(result) = 0 then
                return result;
            else
                return substr(result,1,length(result) - 1);
            end if;
        END;$BODY$
          LANGUAGE plpgsql VOLATILE
          COST 100;
        ALTER FUNCTION fin_get_array_accountid(text)
          OWNER TO openerp;
        '''
        cr.execute(sql)
        return True
    
    def fn_get_prior_rangedate(self, cr):
#         cr.execute("select exists (select 1 from pg_type where typname = 'fn_get_prior_rangedate')")
#         res = cr.fetchone()
#         if res and res[0]:
#             return True
        sql = '''
        DROP FUNCTION IF EXISTS fn_get_prior_rangedate(IN date_get date, IN period_type character varying, OUT start_date date, OUT end_date date) CASCADE;
        commit;
        
        CREATE OR REPLACE FUNCTION fn_get_prior_rangedate(IN date_get date, IN period_type character varying, OUT start_date date, OUT end_date date)
          RETURNS SETOF record AS
        $BODY$
        DECLARE
            _yyyy        int;
        BEGIN
            _yyyy = date_part('year', date_get)::int;
        
            case period_type
                when 'year' then
                    _yyyy = _yyyy - 1;
                    
                    start_date = date(_yyyy::text||'-01-01');
                    end_date = date(_yyyy::text||'-12-31');
                when 'quarter' then
                    case date_part('quarter', date_get)::int
                        when 1 then
                            _yyyy = _yyyy - 1;
                            start_date = date(_yyyy::text||'-10-01');
                            end_date = date(_yyyy::text||'-12-31');
                        when 2 then
                            start_date = date(_yyyy::text||'-01-01');
                            end_date = date(_yyyy::text||'-03-31');
                        when 3 then
                            start_date = date(_yyyy::text||'-04-01');
                            end_date = date(_yyyy::text||'-06-30');
                        else
                            start_date = date(_yyyy::text||'-07-01');
                            end_date = date(_yyyy::text||'-09-30');
                    end case;
        
                else
                    select date_start, date_stop into start_date, end_date
                    from account_period where date_trunc('month',date_start) = date_trunc('month', date(date_trunc('month', date_get))-1);
            end case;
            
            return next;
            
            return;
        END; $BODY$
          LANGUAGE plpgsql VOLATILE
          COST 100
          ROWS 1000;
        ALTER FUNCTION fn_get_prior_rangedate(date, character varying)
          OWNER TO openerp;
        '''
        cr.execute(sql)
        return True
    
    
    def finance_data(self, cr):
        cr.execute("select exists (select 1 from pg_type where typname = 'finance_data')")
        res = cr.fetchone()
        if res and res[0]:
            cr.execute('''delete from pg_type where typname = 'finance_data';
                            delete from pg_class where relname='finance_data';
                            commit;''')
        sql = '''
        CREATE TYPE finance_data AS
           (seq integer,
            doc_no character varying(64),
            description character varying(250),
            gl_date date,
            doc_date date,
            acc_code character varying(12),
            acc_name character varying(150),
            debit numeric,
            credit numeric);
        --ALTER TYPE finance_data
          --OWNER TO openerp;
        '''
        cr.execute(sql)
        return True
    
    def fn_get_account_child_id(self, cr):
#         cr.execute("select exists (select 1 from pg_type where typname = 'fn_get_account_child_id')")
#         res = cr.fetchone()
#         if res and res[0]:
#             return True
        sql = '''
        DROP FUNCTION IF EXISTS fn_get_account_child_id(parent integer) CASCADE;
        commit;
        
        CREATE OR REPLACE FUNCTION fn_get_account_child_id(parent integer)
          RETURNS SETOF account_account AS
        $BODY$
                SELECT  account_account
                FROM    account_account
                WHERE   id = $1
                UNION ALL
                SELECT  fn_get_account_child_id(id)
                FROM    account_account     
                WHERE   parent_id = $1
        $BODY$
          LANGUAGE sql VOLATILE
          COST 100
          ROWS 1000;
        --ALTER FUNCTION fn_get_account_child_id(integer)
          --OWNER TO openerp;
        '''
        cr.execute(sql)
        return True
    
    def fn_cashbank_book_type(self, cr):
        cr.execute("select exists (select 1 from pg_type where typname = 'fin_cash_data')")
        res = cr.fetchone()
        if res and res[0]:
            return True
        sql = '''
        CREATE TYPE fin_cash_data AS
           (seq integer,
            doc_no character varying(64),
            description character varying(250),
            gl_date date,
            doc_date date,
            acc_code character varying(12),
            acc_name character varying(150),
            receipt numeric,
            payment numeric,
            remain numeric,
            note text);
        --ALTER TYPE fin_cash_data
          --OWNER TO openerp;
        '''
        cr.execute(sql)
        return True
    
    def fn_cashbank_begin(self, cr):
#         cr.execute("select exists (select 1 from pg_proc where proname = 'fn_cash_begin')")
#         res = cr.fetchone()
#         if res and res[0]:
#             return True
        sql = '''
        DROP FUNCTION IF EXISTS fn_cash_begin(integer, date) CASCADE;
        commit;
        
        CREATE OR REPLACE FUNCTION fn_cash_begin(integer, date)
          RETURNS SETOF fin_cash_data AS
        $BODY$
                select 0::int as seq, null::text as doc_no, 'Số tồn đầu kỳ'::text as description,
                    null::date as gl_date, null::date as doc_date,
                    null::text as acc_code, null::text as acc_name,
                    case when dr_amount > cr_amount then dr_amount - cr_amount
                        else 0 end as receipt,
                    case when dr_amount < cr_amount then  cr_amount - dr_amount
                        else 0 end as payment,
                    0::numeric as remain, ''::text as note
                from (
                        select sum(debit) dr_amount, sum(credit) cr_amount
                        from (
                            select aml.debit,aml.credit
                            from account_move amh join account_move_line aml 
                                    on amh.id = aml.move_id and amh.state = 'posted'
                                    and aml.state = 'valid' -- and aml.warehouse_id = $3
                                    and to_char(aml.date, 'YYYY') = to_char($2,'YYYY')
                                join account_journal ajn on amh.journal_id = ajn.id
                                    and ajn.type = 'situation'
                                join fn_get_account_child_id($1) acc on aml.account_id = acc.id
                            union all
                            select aml.debit,aml.credit
                            from account_move amh join account_move_line aml 
                                    on amh.id = aml.move_id and amh.state = 'posted'
                                    and aml.state = 'valid' -- and aml.warehouse_id = $3
                                    and date(aml.date) between date(to_char($2,'YYYY')||'-01-01') and date($2-1)
                                join account_journal ajn on amh.journal_id = ajn.id
                                    and ajn.type != 'situation'
                                join fn_get_account_child_id($1) acc on aml.account_id = acc.id
                            ) cashview
                    ) begin_bal
        $BODY$
          LANGUAGE sql VOLATILE
          COST 100
          ROWS 1000;
        --ALTER FUNCTION fn_cash_begin(integer, date)
          --OWNER TO openerp;
        '''
        cr.execute(sql)
        return True
    
    def fn_cashbank_end(self, cr):
#         cr.execute("select exists (select 1 from pg_proc where proname = 'fn_cash_end')")
#         res = cr.fetchone()
#         if res and res[0]:
#             return True
        sql = '''
        DROP FUNCTION IF EXISTS fn_cash_end(integer, date) CASCADE;
        commit;
        
        CREATE OR REPLACE FUNCTION fn_cash_end(integer, date)
          RETURNS SETOF fin_cash_data AS
        $BODY$
                select 999::int as seq, null::text as doc_no, 'Số tồn cuối kỳ'::text as description,
                    null::date as gl_date, null::date as doc_date,
                    null::text as acc_code, null::text as acc_name,
                    case when dr_amount > cr_amount then dr_amount - cr_amount
                        else 0 end as receipt,
                    case when dr_amount < cr_amount then  cr_amount - dr_amount
                        else 0 end as payment,
                    0::numeric as remain, ''::text as note
                from (
                        select sum(debit) dr_amount, sum(credit) cr_amount
                        from (
                            select aml.debit,aml.credit
                            from account_move amh join account_move_line aml 
                                    on amh.id = aml.move_id and amh.state = 'posted'
                                    and aml.state = 'valid' -- and aml.warehouse_id = $3
                                    and date(aml.date) between date(to_char($2,'YYYY')||'-01-01') and date($2)
                                join fn_get_account_child_id($1) acc on aml.account_id = acc.id
                            ) cashview
                    ) begin_bal
        $BODY$
          LANGUAGE sql VOLATILE
          COST 100
          ROWS 1000;
        --ALTER FUNCTION fn_cash_end(integer, date)
          --OWNER TO openerp;
        '''
        cr.execute(sql)
        return True
    
    def fn_cashbank_book_report(self, cr):
#         cr.execute("select exists (select 1 from pg_proc where proname = 'fin_bankcash_report')")
#         res = cr.fetchone()
#         if res and res[0]:
#             return True
        sql = '''
            DROP FUNCTION IF EXISTS fin_bankcash_report(integer, date, date) CASCADE;
            commit;
        
            CREATE OR REPLACE FUNCTION fin_bankcash_report(integer, date, date)
              RETURNS SETOF fin_cash_data AS
            $BODY$
            DECLARE
                _account_id     alias for $1;
                _from_date        alias for $2;
                _to_date        alias for $3;
                --_warehouse_id    alias for $4;
                rec_move        record;
                acc_data        fin_cash_data%ROWTYPE;
                amount            numeric;
                remain            numeric;
                total_dr        numeric;
                total_cr        numeric;
            BEGIN
                -- 1) lay gia tri ton dau ky
                remain = 0;
                select * into rec_move from fn_cash_begin(_account_id, _from_date);--, _warehouse_id);
                if rec_move.seq notnull then
                    remain = rec_move.receipt - rec_move.payment;
                    acc_data.seq = rec_move.seq;
                    acc_data.doc_no = null;
                    acc_data.description = rec_move.description;
                    acc_data.gl_date = null;
                    acc_data.doc_date = null;
                    acc_data.receipt = null;
                    acc_data.payment = null;
                    acc_data.remain = remain;
                    
                    return next acc_data;
                end if;
                
                -- 2) lay thong tin giao dich theo tai khoan so quy tien (111-112)
                total_dr = 0;    total_cr = 0;
                
                for rec_move in select amh.id, coalesce(avh.number,amh.name) entry_no, 
                                    -- coalesce(avh.warehouse_id,amh.warehouse_id) warehouse_id,
                                    coalesce(avh.name,amh.ref) description,
                                    date(amh.date) gl_date,
                                    date(amh.date) doc_date,
                                    --date(amh.date_document) doc_date,
                                    acc.code, acc.name account_name,
                                    sum(aml.debit) dr_amount,
                                    sum(aml.credit) cr_amount,
                                    case when sum(aml.debit) - sum(aml.credit) > 0 
                                        then 1 else 2 end seq,
                                    avh.id voucher_id
                            from account_move amh join account_move_line aml on amh.id = aml.move_id
                                    and amh.state = 'posted' and aml.state = 'valid'
                                    -- and amh.warehouse_id = _warehouse_id
                                    and date(aml.date) between _from_date and _to_date
                                join account_journal ajn on amh.journal_id = ajn.id
                                    and ajn.type != 'situation'
                                join fn_get_account_child_id(_account_id) acc on aml.account_id = acc.id
                                left join account_voucher avh on amh.id = avh.move_id
                            group by amh.id, coalesce(avh.number,amh.name), 
                                    -- coalesce(avh.warehouse_id,amh.warehouse_id),
                                    coalesce(avh.name,amh.ref),
                                    date(amh.date),
                                    date(amh.date),
                                    --date(amh.date_document),
                                    acc.code, acc.name, avh.id
                            order by 5, 11
                loop
                    -- Tinh toán và add dòng chi tiết sổ quỹ
                    amount = rec_move.dr_amount - rec_move.cr_amount;
                    remain = remain + amount;
                    
                    acc_data.seq = rec_move.seq;
                    acc_data.doc_no = rec_move.entry_no;
                    acc_data.description = rec_move.description;
                    acc_data.gl_date = rec_move.gl_date;
                    acc_data.doc_date = rec_move.doc_date;
                    if amount > 0 then
                        acc_data.receipt = amount;
                        acc_data.payment = null;
                        total_dr = total_dr + amount;
                    else
                        acc_data.receipt = null;
                        acc_data.payment = abs(amount);
                        total_cr = total_cr + abs(amount);
                    end if;
                    acc_data.remain = remain;
                    
                    return next acc_data;
                end loop;
                
                -- 3) Add dong sum detail
                acc_data.seq = 99;
                acc_data.doc_no = null;
                acc_data.description = 'Cộng phát sinh trong kỳ';
                acc_data.gl_date = null;
                acc_data.doc_date = null;
                acc_data.receipt = total_dr;
                acc_data.payment = total_cr;
                acc_data.remain = null;
                
                return next acc_data;
                
                -- 4) lay gia tri ton cuoi ky
                select * into rec_move from fn_cash_end(_account_id, _to_date);--, _warehouse_id);
                if rec_move.seq notnull then
                    remain = rec_move.receipt - rec_move.payment;
                    acc_data.seq = rec_move.seq;
                    acc_data.doc_no = null;
                    acc_data.description = rec_move.description;
                    acc_data.gl_date = null;
                    acc_data.doc_date = null;
                    acc_data.receipt = null;
                    acc_data.payment = null;
                    acc_data.remain = remain;
                    
                    return next acc_data;
                end if;
                
                return;
            END; $BODY$
              LANGUAGE plpgsql VOLATILE
              COST 100
              ROWS 1000;
            --ALTER FUNCTION fin_bankcash_report(integer, date, date)
              --OWNER TO openerp;
        '''
        cr.execute(sql)
        return True
    
sql_function()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
