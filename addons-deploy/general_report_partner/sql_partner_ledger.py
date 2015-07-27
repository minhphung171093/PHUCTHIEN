# -*- coding: utf-8 -*-
# #############################################################################
# 
# #############################################################################
import tools
from osv import fields, osv
from tools.translate import _

class sql_partner_ledger(osv.osv):
    _name = "sql.partner.ledger"
    _auto = False
    
    #For reports
    def get_line(self, cr, start_date, end_date, account_id, partner_id):
        sql ='''
            SELECT  gl_date,doc_no,doc_date,description,acc_code,
                nullif(amount_dr,0) amount_dr, nullif(amount_cr,0) amount_cr
            FROM fin_liability_data('%s', '%s', %s, %s);
        '''%(start_date, end_date, account_id, partner_id)
        cr.execute(sql)
        return cr.dictfetchall()
    
    def init(self, cr):
        self.partner_ledger_data(cr)
        self.fin_liability_data(cr)
        cr.commit()
        return True
    
    def partner_ledger_data(self,cr):
        cr.execute("select exists (select 1 from pg_type where typname = 'partner_ledger_data')")
        res = cr.fetchone()
        if res and res[0]:
            cr.execute('''delete from pg_type where typname = 'partner_ledger_data';
                            delete from pg_class where relname='partner_ledger_data';
                            commit;''')
        sql = '''
        CREATE TYPE partner_ledger_data AS
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
        ALTER TYPE partner_ledger_data
          OWNER TO openerp;
        '''
        cr.execute(sql)
        return True  
    
    def fin_liability_data(self,cr):
        sql = '''
        DROP FUNCTION IF EXISTS fin_liability_data(date, date, integer, integer) CASCADE;
        commit;
        
        CREATE OR REPLACE FUNCTION fin_liability_data(date, date, integer, integer)
          RETURNS SETOF partner_ledger_data AS
        $BODY$
        DECLARE
            rec_data    record;
            rec_tmp        record;
            lia_data    partner_ledger_data%ROWTYPE;
            line_no        int;
            beg_amount    numeric;
            end_amount    numeric;
            sum_dr        numeric;
            sum_cr        numeric;
            amt_sign    int;
        BEGIN
            line_no = 1;
            lia_data.seq = line_no;
            lia_data.gl_date = null;
            lia_data.doc_date = null;
            lia_data.doc_no = null;
            lia_data.description = 'Số dư đầu kỳ';
            lia_data.acc_code = null;
            lia_data.acc_name = null;
            lia_data.amount_dr = 0;
            lia_data.amount_cr = 0;
            lia_data.line_type = 0;
            /*    Lay so du dau ky    */
            for rec_data in
                    select sum(beg_dr) begin_dr, sum(beg_cr) begin_cr
                    from (
                            select sum(aml.debit) as beg_dr, sum(aml.credit) as beg_cr 
                            from account_move amh join account_move_line aml on amh.id = aml.move_id
                                    and amh.state = 'posted' and aml.state = 'valid'
                                join account_journal ajn on amh.journal_id = ajn.id
                                    and ajn.type = 'situation'
                                join fn_get_account_child_id($3) acc on aml.account_id = acc.id
                                join res_partner rpt on aml.partner_id = rpt.id /* lien ket voi partner */
                            where date_trunc('year', aml.date) = date_trunc('year', $1::date)
                                    and aml.partner_id = $4
                        union all
                            select sum(aml.debit) as beg_dr, sum(aml.credit) as beg_cr
                            from account_move_line aml join account_move amh on aml.move_id = amh.id
                                    and amh.state = 'posted' and aml.state = 'valid'
                                join account_journal ajn on amh.journal_id = ajn.id
                                    and ajn.type != 'situation'
                                join fn_get_account_child_id($3) acc on aml.account_id = acc.id
                                join res_partner rpt on aml.partner_id = rpt.id /* lien ket voi partner */
                            where aml.date >= date(date_trunc('year', $1::date))
                                and aml.date < $1 and aml.partner_id = $4
                        ) vw
            loop
                beg_amount = coalesce(rec_data.begin_dr,0) - coalesce(rec_data.begin_cr,0);
                end_amount = beg_amount;
            
                if beg_amount >=0 then
                    lia_data.amount_dr = beg_amount;
                else
                    lia_data.amount_cr = -beg_amount;
                end if;
                
                return next lia_data;
            end loop;
            /*    Lay so phat sinh trong ky    */
            sum_dr = 0;        sum_cr = 0;
            for rec_data in
                        select  amh.date, amh.date,
                                case when aih.id notnull then aih.number
                                    when avh.id notnull then avh.number
                                    when amh.ref isnull then aml.name
                                    else amh.name end number,
                                case when aih.id notnull then aih.name
                                    when avh.id notnull then avh.name
                                    else amh.ref end description,
                                aml.move_id, aml.account_id, acc.code, acc.name,
                                sum(aml.debit) amt_dr, sum(aml.credit) amt_cr
                        from account_move_line aml join account_move amh on aml.move_id = amh.id
                                and amh.state = 'posted' and aml.state = 'valid'
                            join account_journal ajn on amh.journal_id = ajn.id
                                and ajn.type != 'situation'
                            join fn_get_account_child_id($3) acc on aml.account_id = acc.id
                            join res_partner rpt on aml.partner_id = rpt.id /* lien ket voi partner */
                            left join account_invoice aih on amh.id = aih.move_id /* lien ket voi invoice */
                            left join account_voucher avh on amh.id = avh.move_id /* lien ket voi payment */
                        where aml.partner_id = $4 and aml.date between $1 and $2
                        group by amh.date, amh.date, aml.move_id,
                                case when aih.id notnull then aih.number
                                    when avh.id notnull then avh.number
                                    when amh.ref isnull then aml.name
                                    else amh.name end,
                                case when aih.id notnull then aih.name
                                    when avh.id notnull then avh.name
                                    else amh.ref end,
                                aml.account_id, acc.code, acc.name
                        order by 1, 3
            loop
                --sum_dr = sum_dr + rec_data.amt_dr;
                --sum_cr = sum_cr + rec_data.amt_cr;
        
                lia_data.gl_date = rec_data.date;
                lia_data.doc_date = rec_data.date;
                lia_data.doc_no = rec_data.number;
                lia_data.description = rec_data.description;
        
                /*    quet du lieu lay doi ung theo tung nghiep vu    */
                if (rec_data.amt_dr > 0) then
                    beg_amount = rec_data.amt_dr;
                    
                    for rec_tmp in    select acc.id, acc.code, acc.name, 
                                        sum(aml.debit) dr_amount, sum(aml.credit) cr_amount
                                    from account_move amh join account_move_line aml 
                                            on amh.id = aml.move_id and amh.id = rec_data.move_id
                                        join account_account acc on aml.account_id = acc.id
                                            and acc.id != rec_data.account_id
                                            and aml.credit > 0
                                    group by acc.id, acc.code, acc.name
                                    order by 2
                    loop
                        exit when beg_amount <= 0;
                        
                        sum_dr = sum_dr + rec_tmp.cr_amount;
                        line_no = line_no + 1;
                        lia_data.seq = line_no;
                        lia_data.line_type = 1;
                        lia_data.acc_code = rec_tmp.code;
                        lia_data.acc_name = rec_tmp.name;
                        lia_data.amount_dr = rec_tmp.cr_amount;
                        lia_data.amount_cr = rec_tmp.dr_amount;
                        
                        if beg_amount < rec_tmp.dr_amount then
                            lia_data.amount_dr = beg_amount;
                        end if;
                        beg_amount = beg_amount - (rec_tmp.dr_amount+rec_tmp.cr_amount);
                        
                        return next lia_data;
                    end loop;
                end if;
                
                if (rec_data.amt_cr > 0) then
                    beg_amount = rec_data.amt_cr;
                    
                    for rec_tmp in    select acc.id, acc.code, acc.name, 
                                        sum(aml.debit) dr_amount, sum(aml.credit) cr_amount
                                    from account_move amh join account_move_line aml 
                                            on amh.id = aml.move_id and amh.id = rec_data.move_id
                                        join account_account acc on aml.account_id = acc.id
                                            and acc.id != rec_data.account_id
                                            and aml.debit > 0
                                    group by acc.id, acc.code, acc.name
                                    order by 2
                    loop
                        exit when beg_amount <= 0;
                        
                        sum_cr = sum_cr + rec_tmp.dr_amount;
                        line_no = line_no + 1;
                        lia_data.seq = line_no;
                        lia_data.line_type = 2;
                        lia_data.acc_code = rec_tmp.code;
                        lia_data.acc_name = rec_tmp.name;
                        lia_data.amount_dr = rec_tmp.cr_amount;
                        lia_data.amount_cr = rec_tmp.dr_amount;
                        
                        if beg_amount < rec_tmp.cr_amount then
                            lia_data.amount_cr = beg_amount;
                        end if;
                        beg_amount = beg_amount - (rec_tmp.dr_amount+rec_tmp.cr_amount);
                        
                        return next lia_data;
                    end loop;
                end if;
            end loop;
            
            end_amount = end_amount + sum_dr - sum_cr;
            /*    Add dong tong phat sinh    */
            line_no = line_no + 1;
            lia_data.seq = line_no;
            lia_data.gl_date = null;
            lia_data.doc_date = null;
            lia_data.doc_no = null;
            lia_data.description = 'Cộng số phát sinh';
            lia_data.acc_code = null;
            lia_data.acc_name = null;
            lia_data.amount_dr = sum_dr;
            lia_data.amount_cr = sum_cr;
            lia_data.line_type = 99;
            return next lia_data;
            /*    Add dong so du cuoi ky    */
            line_no = line_no + 1;
            lia_data.seq = line_no;
            lia_data.gl_date = null;
            lia_data.doc_date = null;
            lia_data.doc_no = null;
            lia_data.description = 'Số dư cuối kỳ';
            lia_data.acc_code = null;
            lia_data.acc_name = null;
            lia_data.amount_dr = 0;
            lia_data.amount_cr = 0;
            lia_data.line_type = 999;
            if end_amount >=0 then
                lia_data.amount_dr = end_amount;
            else
                lia_data.amount_cr = -end_amount;
            end if;
            return next lia_data;
            return;
        END; $BODY$
          LANGUAGE plpgsql VOLATILE
          COST 100
          ROWS 1000;
        ALTER FUNCTION fin_liability_data(date, date, integer, integer)
          OWNER TO openerp;
        '''
        cr.execute(sql)
        return True  
    
sql_partner_ledger()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
