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

class sql_depreciation_asset(osv.osv):
    _name = "sql.depreciation.asset"
    _auto = False
    
    #For report purpose
    def get_line(self, cr, start_date, end_date):
        sql ='''
            select * from fin_assetdepreciation_report('%s','%s')
        '''%(start_date,end_date)
        cr.execute(sql)
        return cr.dictfetchall()
    
    def get_sum_line(self, cr, start_date, end_date):
        sql ='''
             select sum(depreciation_value) depreciation_value, sum(acc_depreciation) acc_depreciation,sum(remaining_value) remaining_value
             from fin_assetdepreciation_report('%s','%s')
        '''%(start_date,end_date)
        cr.execute(sql)
        return cr.dictfetchall()
        
    def init(self, cr):
#         self.fin_assetdepreciation_data(cr)
        self.fin_assetdepreciation_report(cr)
        cr.commit()
        return True
    
    def fin_assetdepreciation_data(self,cr):
        cr.execute("select exists (select 1 from pg_type where typname = 'fin_assetdepreciation_data')")
        res = cr.fetchone()
        if res and res[0]:
            cr.execute('''delete from pg_type where typname = 'fin_assetdepreciation_data';
                            delete from pg_class where relname='fin_assetdepreciation_data';
                            commit;''')
        
        sql = '''
        '''
        cr.execute(sql)
        return True
    
    def fin_assetdepreciation_report(self,cr):
        sql = '''
        DROP FUNCTION IF EXISTS fin_assetdepreciation_report(date, date) CASCADE;
        commit;
        
        CREATE OR REPLACE FUNCTION fin_assetdepreciation_report(IN date, IN date, OUT no integer, OUT code character varying, OUT name character varying, OUT gross_value numeric, OUT number_of_period integer, OUT first_used date, OUT value_of_month numeric, OUT depreciation_value numeric, OUT acc_depreciation numeric, OUT remaining_value numeric, OUT notes character varying, OUT account_analytic character varying)
          RETURNS SETOF record AS
        $BODY$
        DECLARE
         _sdate alias for $1;
         _edate alias for $2;
         rec  record;
         recount int=0;
        BEGIN
         for rec in
          select  aas.code, aas.name, aas.purchase_date first_used, aas.purchase_value gross_value,
            (aas.method_number*aas.method_period) number_of_period,
            round((aas.purchase_value-aas.salvage_value)/
             (nullif(aas.method_number,0)*aas.method_period)) value_of_month,
            dep.depreciation_value, dep.remain_value, aas.salvage_value hold_value,
            swh.name warehouse, aas.note, aaa.name account_analytic
          from account_asset_asset aas 
              join stock_warehouse swh on aas.warehouse_id = swh.id
              join account_analytic_account aaa on aaa.id = aas.account_analytic_id
           join (
            select adl.asset_id, sum(adl.amount) depreciation_value,
             min(adl.remaining_value) remain_value
            from account_asset_depreciation_line adl join account_move amh on adl.move_id = amh.id
            where amh.date between _sdate and _edate
            group by asset_id
            ) dep on aas.id = dep.asset_id
          where aas.asset_type = 'asset' order by aas.code
         loop
          recount = recount + 1;
          "no" = recount;
          code = rec.code;
          name = rec.name;
          gross_value = rec.gross_value;
          number_of_period = rec.number_of_period;
          first_used = rec.first_used;
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
        ALTER FUNCTION fin_assetdepreciation_report(date, date)
          OWNER TO openerp;
        '''
        cr.execute(sql)
        return True

sql_depreciation_asset()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
