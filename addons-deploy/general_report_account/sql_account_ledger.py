# -*- coding: utf-8 -*-
# #############################################################################
# 
# #############################################################################
import tools
from osv import fields, osv
from tools.translate import _

class sql_account_ledger(osv.osv):
    _name = "sql.account.ledger"
    _auto = False
    
    def get_line(self, cr, start_date, end_date, account_id, showdetail, company_id, shop_ids):
        if showdetail:
            sql = '''
                SELECT gl_date, doc_date, doc_no, description, acc_code, 
                    nullif(amount_dr,0) debit, nullif(amount_cr,0) credit
                FROM fin_ledger_report('%s','%s', %s, %s, %s, ARRAY%s::int[]);
            ''' %(start_date, end_date, account_id, showdetail, company_id, shop_ids)
        else:
            sql = '''
                SELECT gl_date, doc_date, doc_no, description, acc_code, 
                    nullif(amount_dr,0) debit, nullif(amount_cr,0) credit, line_type
                FROM fin_ledger_report('%s','%s', %s, %s, %s, ARRAY%s::int[])
                WHERE line_type=0;
            ''' %(start_date, end_date, account_id, showdetail, company_id, shop_ids)
        cr.execute(sql)
        return cr.dictfetchall()
    
    def init(self, cr):
        self.fin_general_data(cr)
        self.fin_ledger_report(cr)
        cr.commit()
        return True
    
    def fin_ledger_report(self,cr):
#         cr.execute("select exists (select 1 from pg_proc where proname = 'fin_trial_balance_report')")
#         res = cr.fetchone()
#         if res and res[0]:
#             return True
        sql = '''
        DROP FUNCTION IF EXISTS fin_ledger_report(date, date, integer, boolean, integer, int[]) CASCADE;
        commit;
        CREATE OR REPLACE FUNCTION fin_ledger_report(date, date, integer, boolean, integer, int[])
          RETURNS SETOF fin_general_data AS
        $BODY$
            /*    Lay so dau ky    */
                select 0 as seq, null::date as gl_date, null::date as doc_date,
                    null::text as doc_no, 'Số dư đầu kỳ' as description,
                    null::text as acc_code, null::text as acc_name,
                    case when dr_amount > cr_amount then dr_amount - cr_amount
                        else null end dr_amount,
                    case when dr_amount < cr_amount then  cr_amount - dr_amount
                        else null end cr_amount,
                    0::int
                from (
                        select sum(debit) dr_amount, sum(credit) cr_amount
                        from (
                            select aml.debit,aml.credit
                            from account_move amh join account_move_line aml
                                    on amh.id = aml.move_id
                                    and amh.shop_id = any($6)
                                    and amh.company_id=$5
                                    and amh.state = 'posted'
                                    and aml.state = 'valid' and date_trunc('year', aml.date) = date_trunc('year', $1)
                                join account_journal ajn on amh.journal_id = ajn.id and ajn.type = 'situation'
                                join fn_get_account_child_id($3) acc on aml.account_id = acc.id
                            union all
                            select aml.debit,aml.credit
                            from account_move amh join account_move_line aml
                                    on amh.id = aml.move_id
                                    and amh.shop_id = any($6)
                                    and amh.company_id=$5
                                    and amh.state = 'posted'
                                    and aml.state = 'valid' and date(aml.date) between
                                    date(date_trunc('year', $1)) and date($1 - 1)
                                join account_journal ajn on amh.journal_id = ajn.id and ajn.type <> 'situation'
                                join fn_get_account_child_id($3) acc on aml.account_id = acc.id
                            )v
                    ) start_bal
            union all
            /*    Lay phat sinh trong ky    */
                (select row_number() over(order by am.date, am.date_document, am.name)::int seq, 
                    am.date gl_date, coalesce(am.date_document,am.date) doc_date, am.name doc_no, 
                    coalesce(aih.comment, coalesce(avh.narration,
                        coalesce(am.narration, am.ref))) description,
                    array_to_string(ARRAY(SELECT DISTINCT a.code
                                          FROM account_move_line m2
                                          LEFT JOIN account_account a ON (m2.account_id=a.id)
                                          WHERE m2.move_id = aml.move_id
                                          AND m2.account_id not in (aml.account_id)), ', ') AS acc_code,
                    array_to_string(ARRAY(SELECT DISTINCT a.name
                                          FROM account_move_line m2
                                          LEFT JOIN account_account a ON (m2.account_id=a.id)
                                          WHERE m2.move_id = aml.move_id
                                          AND m2.account_id not in (aml.account_id)), ' | ') AS acc_name,
                    aml.debit dr_amount, aml.credit cr_amount,
                    1::int
                from account_move_line aml
                    join account_move am on aml.move_id=am.id
            and am.shop_id = any($6)
                        and am.company_id=$5
                        and am.state = 'posted'
                        and aml.state = 'valid' and date(aml.date) between $1 and $2
                    left join account_invoice aih on aml.move_id = aih.move_id -- lien ket voi invoice
                    left join account_voucher avh on aml.move_id = avh.move_id -- lien ket thu/chi
                    join fn_get_account_child_id($3) acc on aml.account_id = acc.id
                order by am.date, am.date_document, am.name, acc_code)
            union all
            /*    Add them dong sum detail    */
                select (count(*) + 1)::int seq, 
                    null::date gl_date, null::date doc_date, null::character varying doc_no, 'Số phát sinh trong kỳ'::character varying description,
                    null::character varying acc_code,
                    null::character varying acc_name,
                    sum(aml.debit) dr_amount, sum(aml.credit) cr_amount,
                    0::int
                from account_move_line aml
                    join account_move am on aml.move_id=am.id
            and am.shop_id = any($6)
                        and am.company_id=$5
                        and am.state = 'posted'
                        and aml.state = 'valid' and date(aml.date) between $1 and $2
                    join fn_get_account_child_id($3) acc on aml.account_id = acc.id
                    
            union all
            /*    Lay so cuoi ky    */
                select 999 as seq, null::date as gl_date, null::date as doc_date,
                    null::text as doc_no, 'Số dư cuối kỳ' as description,
                    null::text as acc_code, null::text as acc_name,
                    case when dr_amount > cr_amount then dr_amount - cr_amount
                        else null end dr_amount,
                    case when dr_amount < cr_amount then  cr_amount - dr_amount
                        else null end cr_amount,
                    0::int
                from (
                        select sum(aml.debit) dr_amount, sum(aml.credit) cr_amount
                        from account_move amh join account_move_line aml 
                                on amh.id = aml.move_id
                                and amh.shop_id = any($6)
                                and amh.company_id=$5
                                and amh.state = 'posted'
                                and aml.state = 'valid' and date(aml.date)
                                between date(date_trunc('year', $2)) and $2
                            join fn_get_account_child_id($3) acc on aml.account_id = acc.id
                    ) end_bal;
        $BODY$
          LANGUAGE sql VOLATILE
          COST 100
          ROWS 1000;
        ALTER FUNCTION fin_ledger_report(date, date, integer, boolean, integer, int[])
          OWNER TO openerp;
        '''
        cr.execute(sql)
        return True
    
    def fin_general_data(self,cr):
        cr.execute("select exists (select 1 from pg_type where typname = 'fin_general_data')")
        res = cr.fetchone()
        if res and res[0]:
            cr.execute('''delete from pg_type where typname = 'fin_general_data';
                            delete from pg_class where relname='fin_general_data';
                            commit;''')
        sql = '''
        CREATE TYPE fin_general_data AS
           (seq integer,
            gl_date date,
            doc_date date,
            doc_no character varying(64),
            description character varying(250),
            acc_code character varying(12),
            acc_name character varying(150),
            amount_dr numeric,
            amount_cr numeric,
            line_type integer);
        ALTER TYPE fin_general_data
          OWNER TO openerp;
        '''
        cr.execute(sql)
        return True  

sql_account_ledger()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
