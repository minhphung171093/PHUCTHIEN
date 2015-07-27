# -*- coding: utf-8 -*-
##############################################################################
#
#    HLVSolution, Open Source Management Solution
#
##############################################################################

import time
import pooler
from osv import osv
from tools.translate import _
import random
from datetime import datetime
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
DATE_FORMAT = "%Y-%m-%d"
import tools
from osv import fields, osv

class product_list_allview(osv.osv):
    _name = "product.list.allview"
    _description = "Product List Allview"
    _auto = False
    _columns = {
                'supplier_id':fields.many2one('res.partner','Supplier', select=True,readonly=True),
                'blanket_ref':fields.char('Blanket Ref', size=100, readonly=True),
                'blanket_id':fields.many2one('purchase.blanket.site','Blanket Ref',  size=100, readonly=True),
                'cat':fields.char('Blanket Ref', size=300, readonly=True),
                'categ_id':fields.many2one('product.category','Category', select=True,readonly=True),
                'product_id':fields.many2one('product.product','Product',select=True,readonly=True),
                'uom_id':fields.many2one('product.uom','Uom', select=True,readonly=True),
                'barcode':fields.char('Barcode', size=100, readonly=True),
                'product_code': fields.char('Product Code', size=100, readonly=True),
                'convert_rate':fields.float('Pack Rate'),
                'pack_uom':fields.char('Pack', size=100, readonly=True),
                'input_tax':fields.float('Input Tax'),
                'output_tax':fields.float('Output Tax'),
                'po_price':fields.float('Po Price'),
                'so_price':fields.float('So Price'),
                'status': fields.selection([('',''),
                ('draft', 'In Development'),
                ('sellable','Normal'),
                ('end','End of Lifecycle'),
                ('obsolete','Obsolete')], 'status',),
                }
    def init(self, cr):
        #tools.sql.drop_view_if_exists(cr, 'stock_transact_detail_report')
        tools.sql.drop_view_if_exists(cr, 'stock_details_analys')
        sql = """
            create or replace view product_list_allview as 
            (
                select  row_number() over (order by msi.supplier,
                        msi.blanket_ref, msi.cat_code,
                        msi.product_code) id,
                        msi.supplier,
                        msi.supplier_id,
                        msi.blanket_ref,
                        msi.blanket_id,
                        msi.cat_code||'-'||msi.cat_name cat,
                        msi.categ_id,
                        msi.product_id,
                        msi.uom_id,
                        msi.barcode, msi.product_code,
                        msi.product_name,msi.uom_name,
                        msi.convert_rate, msi.pack_uom,
                        msi.input_tax, msi.output_tax,
                        (msi.po_price/msi.po_convert)::numeric po_price,
                        (msi.sale_price/msi.so_convert)::numeric so_price,
                        msi.status
                        
                from (
                        select ppp.id product_id, ppp.ean13 barcode,
                            ppt.name product_name,ppt.state status,
                            ppp.default_code product_code, ppt.uom_id,
                            uom.name uom_name, ucv.convert_rate,
                             ucv.pack_id, ucv.pack_uom pack_uom,
                            ppp.active, ppt.categ_id,
                            cat.category_code cat_code, cat.name cat_name,
                            (sact.amount*100) input_tax, (cact.amount*100) output_tax
                            , rpn.id supplier_id, rpn.ref||'-'||rpn.name supplier,
                            pbs.id blanket_id,pbs.name blanket_ref,ppi.product_ean po_ean,
                            psi.uom_conversion po_convert, psi.product_uom uop,
                            coalesce(ppi.price,psi.unit_price) po_price
                            , spll.product_ean so_ean, spll.product_uom uos,
                            puc.factor so_convert, 
                            spll.product_value sale_price
                        from product_template ppt join product_product ppp
                                on ppt.id = ppp.product_tmpl_id
                                and (ppp.active = true or true isnull)
                                   and ppp.expense_pdt = false
                                   and ppp.income_pdt = false                                 
                            join product_uom uom on ppt.uom_id = uom.id
                            join fn_get_category_child_id(265) cat
                                on ppt.categ_id = cat.id
                            /*    Ket noi conversion    */
                            left join product_uom_conversion_vl ucv
                                on ppp.id = ucv.id and ppt.uom_id = ucv.pri_id
                                and ucv.pri_id <> ucv.pack_id and ucv.pack_id <> 58
                            /*    Ket noi tax dau vao    */
                            left join product_supplier_taxes_rel str on ppt.id = str.prod_id
                            left join account_tax sact on str.tax_id = sact.id
                            /*    Ket noi tax dau ra    */
                            left join product_taxes_rel ctr on ppt.id = ctr.prod_id
                            left join account_tax cact on ctr.tax_id = cact.id
                            /*    Ket noi barcode    */
                            left join product_barcode pbc 
                                on ppp.id = pbc.product_id
                                   and pbc.uom_id = coalesce(ucv.pack_id, ppt.uom_id)
                            /*    Ket noi Supplier & bang gia mua    */
                            left join (
                                purchase_blanket_site pbs join res_partner rpn
                                    on pbs.partner_id = rpn.id
                                    and current_date between coalesce(pbs.start_date,current_date)
                                        and coalesce(pbs.end_date,current_date)
                                join product_supplierinfo psi 
                                    on pbs.id = psi.site_id and
                                    coalesce(psi.expiration_date,current_date) >= current_date
                                left join pricelist_partnerinfo ppi on psi.id = ppi.suppinfo_id
                                    and ppi.warehouse_id isnull and ppi.product_ean isnull
                                    and current_date between 
                                        coalesce(ppi.start_date,current_date)
                                    and coalesce(ppi.end_date,current_date)
                                ) on ppp.id = psi.product_id 
                            /*    Ket noi bang gia ban    */
                            left join (
                                sale_pricelist splh join sale_pricelist_lines spll
                                    on splh.id = spll.pricelist_id and splh.id = 7 /* bang gia ban PoS */
                                    and current_date between 
                                        coalesce(splh.start_date_active, current_date)
                                    and coalesce(splh.end_date_active, current_date)
                                    and spll.product_attribute = 'product'
                                    and current_date between
                                        coalesce(spll.start_date_active, current_date)
                                    and coalesce(spll.end_date_active, current_date)
                                join product_uom_conversion puc
                                    on spll.product_id = puc.product_id
                                    and spll.product_uom = puc.from_uom_id
                            ) on ppp.id = spll.product_id                        
                    ) msi)
        """
        cr.execute(sql)
product_list_allview()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
