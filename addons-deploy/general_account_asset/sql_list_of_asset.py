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

class sql_list_of_asset(osv.osv):
    _name = "sql.list.of.asset"
    _auto = False
    
    #For reports
    def get_line(self, cr, start_date, end_date, asset_type):
        sql ='''
            select no,voucher_number,voucher_date,code,name,first_used,gross_value,
                   number_of_period,value_of_month,notes, account_analytic from fin_listofasset_report('%s','%s', '%s')
        '''%(start_date, end_date, asset_type)
        cr.execute(sql)
        return cr.dictfetchall()
    
    def get_sum_line(self, cr, start_date, end_date, asset_type):
        sql ='''
              select sum(gross_value) gross_value, sum(value_of_month)  value_of_month
             from fin_listofasset_report('%s','%s', '%s')
        '''%(start_date, end_date, asset_type)
        cr.execute(sql)
        return cr.dictfetchall()
    
    def init(self, cr):
#         self.fin_listofasset_data(cr)
        self.fin_listofasset_report(cr)
        cr.commit()
        return True
    
    def fin_listofasset_data(self,cr):
        cr.execute("select exists (select 1 from pg_type where typname = 'fin_listofasset_data')")
        res = cr.fetchone()
        if res and res[0]:
            cr.execute('''delete from pg_type where typname = 'fin_listofasset_data';
                            delete from pg_class where relname='fin_listofasset_data';
                            commit;''')
        
        sql = '''
        '''
        cr.execute(sql)
        return True
    
    def fin_listofasset_report(self,cr):
        sql = '''
        DROP FUNCTION IF EXISTS fin_listofasset_report(date, date, character varying) CASCADE;
        commit;
        
        CREATE OR REPLACE FUNCTION fin_listofasset_report(IN date, IN date, IN character varying, OUT no integer, OUT voucher_number character varying, OUT voucher_date date, OUT code character varying, OUT name character varying, OUT first_used date, OUT gross_value numeric, OUT number_of_period integer, OUT value_of_month numeric, OUT notes character varying, OUT account_analytic character varying)
          RETURNS SETOF record AS
        $BODY$
        DECLARE
         _sdate alias for $1;
         _edate alias for $2;
         _type  alias for $3;
         rec  record;
         recount int=0;
        BEGIN
         for rec in
          select  aas.voucher_number, aas.voucher_date, aas.code, aas.name, aas.asset_type,
            aas.purchase_date first_used, aas.purchase_value gross_value,
            (aas.method_number*aas.method_period) number_of_period,
            round((aas.purchase_value-aas.salvage_value)/
             (nullif(aas.method_number,0)*aas.method_period)) value_of_month,
            swh.name warehouse,aas.note, aas.salvage_value hold_value,
            aas.method_time, aas.method_number, aas.method_period, aaa.name account_analytic
          from account_asset_asset aas 
              left join stock_warehouse swh on aas.warehouse_id = swh.id
              left join account_analytic_account aaa on aaa.id = aas.account_analytic_id
          where aas.asset_type = _type and aas.purchase_date between _sdate and _edate
          order by aas.code
         loop
          recount = recount + 1;
          "no" = recount;
          voucher_number = rec.voucher_number;
          voucher_date = rec.voucher_date;
          code = rec.code;
          name = rec.name;
          first_used = rec.first_used;
          gross_value = rec.gross_value;
          number_of_period = rec.number_of_period;
          value_of_month = rec.value_of_month;
          notes = 'BPSD: '||rec.warehouse;
          account_analytic = rec.account_analytic;
          
          return next;
         end loop;
         
         return;
        END; $BODY$
          LANGUAGE plpgsql VOLATILE
          COST 100
          ROWS 1000;
        ALTER FUNCTION fin_listofasset_report(date, date, character varying)
          OWNER TO openerp;
        '''
        cr.execute(sql)
        return True

sql_list_of_asset()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
