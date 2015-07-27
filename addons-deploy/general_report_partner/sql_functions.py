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

class sql_function_general_report_partner(osv.osv):
    _name = "sql.function.general.report.partner"
    _auto = False
    
    def init(self, cr):
        self.fn_get_account_child_id(cr)
        self.fn_get_account_parent_id(cr)
        self.fn_get_account_liability(cr)
        
        cr.commit()
    
    def fn_get_account_child_id(self, cr):
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
    
    def fn_get_account_parent_id(self, cr):
        sql = '''
        DROP FUNCTION IF EXISTS fn_get_account_parent_id(integer) CASCADE;
        commit;
        
        CREATE OR REPLACE FUNCTION fn_get_account_parent_id(integer)
          RETURNS SETOF account_account AS
        $BODY$
            SELECT  account_account
            FROM    account_account
            WHERE   id = $1
            UNION ALL
            SELECT  fn_get_account_parent_id(parent_id)
            FROM    account_account     
            WHERE   id = $1
        $BODY$
          LANGUAGE sql VOLATILE
          COST 100
          ROWS 1000;
        ALTER FUNCTION fn_get_account_parent_id(integer)
          OWNER TO openerp;
        '''
        cr.execute(sql)
        return True
    
    def fn_get_account_liability(self, cr):
        sql = '''
        DROP FUNCTION IF EXISTS fn_get_account_liability() CASCADE;
        commit;
        
        CREATE OR REPLACE FUNCTION fn_get_account_liability()
          RETURNS SETOF account_account AS
        $BODY$
        DECLARE
            rec record;
            _id    int;
        BEGIN
            for _id in select id from account_account where type in ('payable','receivable')
            loop
                for rec in select distinct* from fn_get_account_parent_id(_id) where "level" >= 2
                loop
                    return next rec;
                end loop;
            end loop;
            
            return;
        END; $BODY$
          LANGUAGE plpgsql VOLATILE
          COST 100
          ROWS 1000;
        ALTER FUNCTION fn_get_account_liability()
          OWNER TO openerp;
        '''
        cr.execute(sql)
        return True
    
    
sql_function_general_report_partner()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
