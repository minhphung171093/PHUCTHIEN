# -*- coding: utf-8 -*-
# #############################################################################
# 
# #############################################################################
import tools
from osv import fields, osv
from tools.translate import _
import logging
_logger = logging.getLogger(__name__)

class sql_expense_allocation(osv.osv):
    _name = "sql.expense.allocation"
    _auto = False
    
    #For report
    def get_line(self, cr, start_date, end_date, type):
        sql ='''
            SELECT no,code,name,voucher_number,voucher_date,gross_value,number_of_period,value_of_month,
                depreciation_value,acc_depreciation,remaining_value,notes , account_analytic
            FROM fin_expense_allocation_report('%s', '%s', '%s')
        '''%(start_date, end_date, type)
        cr.execute(sql)
        return cr.dictfetchall()
    
    def get_sum_line(self, cr, start_date, end_date, type):
        sql ='''
              select sum(gross_value) gross_value, sum(depreciation_value)  depreciation_value,
                     sum(acc_depreciation) acc_depreciation,sum(remaining_value) remaining_value
             FROM fin_expense_allocation_report('%s', '%s', '%s')
        '''%(start_date, end_date, type)
        cr.execute(sql)
        return cr.dictfetchall()
    
    def init(self, cr):
#         self.fin_assetdepreciation_data(cr)
        self.fin_get_array_accountid(cr)
        self.fin_expense_allocation_report(cr)
        cr.commit()
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
    
    def fin_expense_allocation_data(self,cr):
        cr.execute("select exists (select 1 from pg_type where typname = 'fin_expense_allocation_data')")
        res = cr.fetchone()
        if res and res[0]:
            cr.execute('''delete from pg_type where typname = 'fin_expense_allocation_data';
                            delete from pg_class where relname='fin_expense_allocation_data';
                            commit;''')
        
        sql = '''
        '''
        cr.execute(sql)
        return True
    
    def fin_expense_allocation_report(self,cr):
        sql = '''
        DROP FUNCTION IF EXISTS fin_expense_allocation_report(date, date, character varying) CASCADE;
        commit;
        
        CREATE OR REPLACE FUNCTION fin_expense_allocation_report(IN date, IN date, IN character varying, OUT no integer, OUT code character varying, OUT name character varying, OUT voucher_number character varying, OUT voucher_date date, OUT gross_value numeric, OUT number_of_period integer, OUT value_of_month numeric, OUT depreciation_value numeric, OUT acc_depreciation numeric, OUT remaining_value numeric, OUT notes character varying, OUT account_analytic character varying)
          RETURNS SETOF record AS
        $BODY$
        DECLARE
         _sdate alias for $1;
         _edate alias for $2;
         _type alias for $3;
         rec  record;
         recount int=0;
         lst_account text = 'null';
        BEGIN
         if (_type = 'short term') then
          lst_account = fin_get_array_accountid('142');
         elsif (_type = 'long term') then
          lst_account = fin_get_array_accountid('242');
         end if;
         
         for rec in execute '
          select  aas.code, aas.name, aas.purchase_date first_used, aas.purchase_value gross_value,
            aas.voucher_number, aas.voucher_date, (aas.method_number*aas.method_period) number_of_period,
            round((aas.purchase_value-aas.salvage_value)/
             (nullif(aas.method_number,0)*aas.method_period)) value_of_month,
            dep.depreciation_value, dep.remain_value, aas.salvage_value hold_value,
            swh.name warehouse, aas.note, aaa.name account_analytic
          from account_asset_asset aas join account_asset_category aac
           on aas.category_id = aac.id and aac.account_depreciation_id in ('||lst_account||')
           join stock_warehouse swh on aas.warehouse_id = swh.id
           join account_analytic_account aaa on aaa.id = aas.account_analytic_id
           join (
            select adl.asset_id, sum(adl.amount) depreciation_value,
             min(adl.remaining_value) remain_value
            from account_asset_depreciation_line adl join account_move amh on adl.move_id = amh.id
            where amh.date between date($1) and date($2) group by asset_id
            ) dep on aas.id = dep.asset_id
          where aas.asset_type = ''prepaid'' order by aas.code' using _sdate, _edate
         loop
          recount = recount + 1;
          "no" = recount;
          code = rec.code;
          name = rec.name;
          voucher_number = rec.voucher_number;
          voucher_date = rec.voucher_date;
          gross_value = rec.gross_value;
          number_of_period = rec.number_of_period;
          value_of_month = rec.value_of_month;
          depreciation_value = rec.depreciation_value;
          acc_depreciation = (rec.gross_value - rec.remain_value);
          remaining_value = rec.remain_value;
          notes = rec.note;
          account_analytic = rec.account_analytic;
          
          return next;
         end loop;
         
         return;
        END; $BODY$
          LANGUAGE plpgsql VOLATILE
          COST 100
          ROWS 1000;
        ALTER FUNCTION fin_expense_allocation_report(date, date, character varying)
          OWNER TO openerp;
        '''
        cr.execute(sql)
        return True

sql_expense_allocation()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
