import time
from lxml import etree
from openerp.osv import fields, osv
import openerp.addons.decimal_precision as dp
from openerp.tools import float_compare
import netsvc
from openerp import tools
from openerp.tools.translate import _

class account_voucher(osv.osv):
    _inherit = 'account.voucher'
    _columns = {}
    
    def print_uynhiemchi(self, cr, uid, ids, context=None): 
        return {
                'type': 'ir.actions.report.xml',
                'report_name': 'general_report_uy_nhiem_chi',
            }
account_voucher()

class account_voucher_batch(osv.osv):
    _inherit = 'account.voucher.batch'
    _columns={}
    
    def print_uynhiemchi_bank(self, cr, uid, ids, context=None): 
        return {
                'type': 'ir.actions.report.xml',
                'report_name': 'general_report_uy_nhiem_chi_bank',
            }
        
account_voucher_batch()
    
