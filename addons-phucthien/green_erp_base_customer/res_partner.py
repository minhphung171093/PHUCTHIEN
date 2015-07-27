# -*- coding: utf-8 -*-################################################################################    OpenERP, Open Source Management Solution#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).##    This program is free software: you can redistribute it and/or modify#    it under the terms of the GNU Affero General Public License as#    published by the Free Software Foundation, either version 3 of the#    License, or (at your option) any later version.##    This program is distributed in the hope that it will be useful,#    but WITHOUT ANY WARRANTY; without even the implied warranty of#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the#    GNU Affero General Public License for more details.##    You should have received a copy of the GNU Affero General Public License#    along with this program.  If not, see <http://www.gnu.org/licenses/>.###############################################################################import timefrom openerp.osv import fields, osvfrom openerp.tools.translate import _from datetime import datetimeimport openerp.addons.decimal_precision as dpfrom xlrd import open_workbook,xldate_as_tupleimport osfrom openerp import modulesbase_path = os.path.dirname(modules.get_module_path('green_erp_base_customer'))class res_country_state(osv.osv):    _inherit = "res.country.state"    _columns = {#         'quan_huyen_lines': fields.one2many('res.city', 'state_id', 'Quận/huyện'),    }    def init(self, cr):        country_obj = self.pool.get('res.country')        wb = open_workbook(base_path + '/green_erp_base_customer/data/TinhTP.xls')        for s in wb.sheets():            if (s.name =='Sheet1'):                for row in range(1,s.nrows):                    val0 = s.cell(row,0).value                    val1 = s.cell(row,1).value                    val2 = s.cell(row,2).value                    country_ids = country_obj.search(cr, 1, [('code','=',val2)])                    if country_ids:                        state_ids = self.search(cr, 1, [('name','=',val1),('code','=',val0),('country_id','in',country_ids)])                        if not state_ids:                            self.create(cr, 1, {'name': val1,'code':val0,'country_id':country_ids[0]})        res_country_state()class res_city(osv.osv):    _name = 'res.city'    _columns = {        'name': fields.char('Name', size=128, required=True),        'state_id': fields.many2one('res.country.state', 'State'),        'country_id': fields.related('state_id', 'country_id', type='many2one', readonly=True, relation='res.country', string='Country'),        'postcode_line': fields.one2many('postal.code', 'city_id', 'Postal Codes')    }        def init(self, cr):        state_obj = self.pool.get('res.country.state')        wb = open_workbook(base_path + '/green_erp_base_customer/data/QuanHuyen.xls')        for s in wb.sheets():            if (s.name =='Sheet1'):                for row in range(1,s.nrows):                    val0 = s.cell(row,0).value                    val1 = s.cell(row,1).value                    state_ids = state_obj.search(cr, 1, [('name','=',val1)])                    if state_ids:                        quan_huyen_ids = self.search(cr, 1, [('name','=',val0),('state_id','in',state_ids)])                        if not quan_huyen_ids:                            self.create(cr, 1, {'name': val0,'state_id':state_ids[0]})    res_city()    class postal_code(osv.osv):    _name = 'postal.code'    _columns = {        'name': fields.char('Postal Code', size=128, required=True),        'city_id': fields.many2one('res.city', 'City', ondelete='cascade', required=True)    }    postal_code()class res_partner(osv.osv):    _inherit = "res.partner"    _columns = {        'country_id': fields.many2one('res.country', 'Country'),        'state_id': fields.many2one("res.country.state", 'State', domain="[('country_id','=',country_id)]"),        'city': fields.many2one('res.city', 'City', domain="[('state_id','=',state_id)]"),        'zip': fields.many2one('postal.code', 'Zip', change_default=True, domain="[('city_id','=',city)]"),        'vat': fields.char('MST', size=32, help="Tax Identification Number. Check the box if this contact is subjected to taxes. Used by the some of the legal statements."),        'gsk_code': fields.char('Mã Khách Hàng', size=50),        'kv_benh_vien':fields.many2one('kv.benh.vien','Khu vực bệnh viện')    }        _defaults = {        'type': 'default', # type 'default' is wildcard and thus inappropriate        'date': time.strftime('%Y-%m-%d'),    }        def onchange_country_id(self, cr, uid, ids, country_id, context=None):        value = {'state_id':False,'city':False,'zip':False}#         if country_id:#             country = self.pool.get('res.country').browse(cr, uid, country_id)#             phone_code = country.phone_code#             company_id = country.company_id.id#             value.update({'phone':phone_code,'company_id':company_id, 'default_shipping_id': country.default_shipping_id.id or False})        return {'value':value}        def onchange_state(self, cr, uid, ids, state_id, context=None):        return {'value':{'city':False,'zip':False}}        def onchange_city(self, cr, uid, ids, city, context=None):        return {'value':{'zip':False}}    #     def create(self, cr, uid, vals, context=None):#         country_pool = self.pool.get('res.country')#         if vals.get('country_id',False):#             vals.update({'image':country_pool.read(cr, uid, vals['country_id'], ['flag'])['flag']})#         return super(res_partner, self).create(cr, uid, vals, context=context)#     #     def write(self, cr, uid, ids, vals, context=None):#         country_pool = self.pool.get('res.country')#         if vals.get('country_id',False):#             vals.update({'image':country_pool.read(cr, uid, vals['country_id'], ['flag'])['flag']})#         return super(res_partner, self).write(cr, uid, ids, vals, context=context)        def address_get(self, cr, uid, ids, adr_pref=None, context=None):        """ Find contacts/addresses of the right type(s) by doing a depth-first-search        through descendants within company boundaries (stop at entities flagged ``is_company``)        then continuing the search at the ancestors that are within the same company boundaries.        Defaults to partners of type ``'default'`` when the exact type is not found, or to the        provided partner itself if no type ``'default'`` is found either. """        adr_pref = set(adr_pref or [])        if 'default' not in adr_pref:            adr_pref.add('default')        result = {}        visited = set()        for partner in self.browse(cr, uid, filter(None, ids), context=context):            current_partner = partner            while current_partner:                to_scan = [current_partner]                # Scan descendants, DFS                while to_scan:                    record = to_scan.pop(0)                    visited.add(record)                    if record.type in adr_pref and not result.get(record.type):                        result[record.type] = record.id                    #Thanh: Get default for contact instead of company                    if record.type == 'default' and record.id != partner.id:                        result[record.type] = record.id                    if len(result) == len(adr_pref):                        return result                    to_scan = [c for c in record.child_ids                                 if c not in visited                                 if not c.is_company] + to_scan                # Continue scanning at ancestor if current_partner is not a commercial entity                if current_partner.is_company or not current_partner.parent_id:                    break                current_partner = current_partner.parent_id        # default to type 'default' or the partner itself        default = result.get('default', partner.id)        for adr_type in adr_pref:            result[adr_type] = result.get(adr_type) or default         return result        def show_street_city(self, cr, uid, ids, context=None):        if context is None:            context = {}        if isinstance(ids, (int, long)):            ids = [ids]        res = []        for record in self.browse(cr, uid, ids, context=context):            name = record.parent_id and record.parent_id.name + ' / ' or ''            name += record.name + ' / '            name += record.street and record.street + ' / ' or ''            name += record.city and record.city.name + ' / ' or ''            if name:                name = name[:-3]            res.append((record.id, name))        return res        def name_search(self, cr, uid, name, args=None, operator='ilike', context=None, limit=100):        if not args:            args = []        if not context:            context = {}        contact_ids = []        if context.get('parent_company_id',False):            contact_ids = self.search(cr, uid, [('parent_id','=',context['parent_company_id'])], limit=limit, context=context)            args += [('parent_id','!=',context['parent_company_id'])]        if name:            # Be sure name_search is symetric to name_get            name = name.split(' / ')[-1]            ids = self.search(cr, uid, [('name', operator, name)] + args, limit=limit, context=context)        else:            ids = self.search(cr, uid, args, limit=limit, context=context)                        ids = contact_ids + ids        if context.get('show_street_city',False):            return self.show_street_city(cr, uid, ids, context)        else:            return self.name_get(cr, uid, ids, context)        def name_get(self, cr, uid, ids, context=None):        if context is None:            context = {}        if isinstance(ids, (int, long)):            ids = [ids]        res = []        for record in self.browse(cr, uid, ids, context=context):            name = record.name#             if record.parent_id and not record.is_company:#                 name =  "%s, %s" % (record.parent_id.name, name)            if context.get('show_address'):                name = name + "\n" + self._display_address(cr, uid, record, without_company=True, context=context)                name = name.replace('\n\n','\n')                name = name.replace('\n\n','\n')            if context.get('show_email') and record.email:                name = "%s <%s>" % (name, record.email)            res.append((record.id, name))        return res        #Thanh: Redisplay Address    def _display_address(self, cr, uid, address, without_company=False, context=None):        '''        The purpose of this function is to build and return an address formatted accordingly to the        standards of the country where it belongs.        :param address: browse record of the res.partner to format        :returns: the address formatted in a display that fit its country habits (or the default ones            if not country is specified)        :rtype: string        '''        # get the information that will be injected into the display format        # get the address format#         address_format = "%(street)s, %(street2)s, %(city_name)s, %(state_name)s, %(zip_name)s, %(country_name)s"        address_format = "%(company_name)s / %(street)s / %(street2)s / %(city_name)s"        args = {            'city_name': address.city.name or '',            'zip_name': address.zip.name or '',            'state_code': address.state_id and address.state_id.code or '',            'state_name': address.state_id and address.state_id.name or '',            'country_code': address.country_id and address.country_id.code or '',            'country_name': address.country_id and address.country_id.name or '',            'company_name': address.parent_id and address.parent_id.name or '',        }        for field in self._address_fields(cr, uid, context=context):            args[field] = getattr(address, field) or ''#         if without_company:#             args['company_name'] = ''#         elif address.parent_id:#             #Thanh: No need to show compnay name# #             address_format = '%(company_name)s\n' + address_format#             address_format = address_format        return address_format % args    res_partner()class kv_benh_vien(osv.osv):    _name = 'kv.benh.vien'    _columns = {        'name': fields.char('Tên', size=1024, required=True),        }    kv_benh_vien()class res_country_state(osv.osv):    _inherit = "res.country.state"    _columns = {#         'quan_huyen_lines': fields.one2many('res.city', 'state_id', 'Quận/huyện'),    }    def init(self, cr):        country_obj = self.pool.get('res.country')        wb = open_workbook(base_path + '/green_erp_base_customer/data/TinhTP.xls')        for s in wb.sheets():            if (s.name =='Sheet1'):                for row in range(1,s.nrows):                    val0 = s.cell(row,0).value                    val1 = s.cell(row,1).value                    val2 = s.cell(row,2).value                    country_ids = country_obj.search(cr, 1, [('code','=',val2)])                    if country_ids:                        state_ids = self.search(cr, 1, [('name','=',val1),('code','=',val0),('country_id','in',country_ids)])                        if not state_ids:                            self.create(cr, 1, {'name': val1,'code':val0,'country_id':country_ids[0]})        res_country_state()class res_city(osv.osv):    _name = 'res.city'    _columns = {        'name': fields.char('Name', size=128, required=True),        'state_id': fields.many2one('res.country.state', 'State'),        'country_id': fields.related('state_id', 'country_id', type='many2one', readonly=True, relation='res.country', string='Country'),        'postcode_line': fields.one2many('postal.code', 'city_id', 'Postal Codes')    }        def init(self, cr):        state_obj = self.pool.get('res.country.state')        wb = open_workbook(base_path + '/green_erp_base_customer/data/QuanHuyen.xls')        for s in wb.sheets():            if (s.name =='Sheet1'):                for row in range(1,s.nrows):                    val0 = s.cell(row,0).value                    val1 = s.cell(row,1).value                    state_ids = state_obj.search(cr, 1, [('name','=',val1)])                    if state_ids:                        quan_huyen_ids = self.search(cr, 1, [('name','=',val0),('state_id','in',state_ids)])                        if not quan_huyen_ids:                            self.create(cr, 1, {'name': val0,'state_id':state_ids[0]})    res_city()    class postal_code(osv.osv):    _name = 'postal.code'    _columns = {        'name': fields.char('Postal Code', size=128, required=True),        'city_id': fields.many2one('res.city', 'City', ondelete='cascade', required=True)    }    postal_code()class res_partner(osv.osv):    _inherit = "res.partner"    _columns = {        'country_id': fields.many2one('res.country', 'Country'),        'state_id': fields.many2one("res.country.state", 'State', domain="[('country_id','=',country_id)]"),        'city': fields.many2one('res.city', 'City', domain="[('state_id','=',state_id)]"),        'zip': fields.many2one('postal.code', 'Zip', change_default=True, domain="[('city_id','=',city)]"),        'vat': fields.char('MST', size=32, help="Tax Identification Number. Check the box if this contact is subjected to taxes. Used by the some of the legal statements."),    }        _defaults = {        'type': 'default', # type 'default' is wildcard and thus inappropriate        'date': time.strftime('%Y-%m-%d'),    }        def onchange_country_id(self, cr, uid, ids, country_id, context=None):        value = {'state_id':False,'city':False,'zip':False}#         if country_id:#             country = self.pool.get('res.country').browse(cr, uid, country_id)#             phone_code = country.phone_code#             company_id = country.company_id.id#             value.update({'phone':phone_code,'company_id':company_id, 'default_shipping_id': country.default_shipping_id.id or False})        return {'value':value}        def onchange_state(self, cr, uid, ids, state_id, context=None):        return {'value':{'city':False,'zip':False}}        def onchange_city(self, cr, uid, ids, city, context=None):        return {'value':{'zip':False}}    #     def create(self, cr, uid, vals, context=None):#         country_pool = self.pool.get('res.country')#         if vals.get('country_id',False):#             vals.update({'image':country_pool.read(cr, uid, vals['country_id'], ['flag'])['flag']})#         return super(res_partner, self).create(cr, uid, vals, context=context)#     #     def write(self, cr, uid, ids, vals, context=None):#         country_pool = self.pool.get('res.country')#         if vals.get('country_id',False):#             vals.update({'image':country_pool.read(cr, uid, vals['country_id'], ['flag'])['flag']})#         return super(res_partner, self).write(cr, uid, ids, vals, context=context)        def address_get(self, cr, uid, ids, adr_pref=None, context=None):        """ Find contacts/addresses of the right type(s) by doing a depth-first-search        through descendants within company boundaries (stop at entities flagged ``is_company``)        then continuing the search at the ancestors that are within the same company boundaries.        Defaults to partners of type ``'default'`` when the exact type is not found, or to the        provided partner itself if no type ``'default'`` is found either. """        adr_pref = set(adr_pref or [])        if 'default' not in adr_pref:            adr_pref.add('default')        result = {}        visited = set()        for partner in self.browse(cr, uid, filter(None, ids), context=context):            current_partner = partner            while current_partner:                to_scan = [current_partner]                # Scan descendants, DFS                while to_scan:                    record = to_scan.pop(0)                    visited.add(record)                    if record.type in adr_pref and not result.get(record.type):                        result[record.type] = record.id                    #Thanh: Get default for contact instead of company                    if record.type == 'default' and record.id != partner.id:                        result[record.type] = record.id                    if len(result) == len(adr_pref):                        return result                    to_scan = [c for c in record.child_ids                                 if c not in visited                                 if not c.is_company] + to_scan                # Continue scanning at ancestor if current_partner is not a commercial entity                if current_partner.is_company or not current_partner.parent_id:                    break                current_partner = current_partner.parent_id        # default to type 'default' or the partner itself        default = result.get('default', partner.id)        for adr_type in adr_pref:            result[adr_type] = result.get(adr_type) or default         return result        def show_street_city(self, cr, uid, ids, context=None):        if context is None:            context = {}        if isinstance(ids, (int, long)):            ids = [ids]        res = []        for record in self.browse(cr, uid, ids, context=context):            name = record.parent_id and record.parent_id.name + ' / ' or ''            name += record.name + ' / '            name += record.street and record.street + ' / ' or ''            name += record.city and record.city.name + ' / ' or ''            if name:                name = name[:-3]            res.append((record.id, name))        return res        def name_search(self, cr, uid, name, args=None, operator='ilike', context=None, limit=100):        if not args:            args = []        if not context:            context = {}        contact_ids = []        if context.get('parent_company_id',False):            contact_ids = self.search(cr, uid, [('parent_id','=',context['parent_company_id'])], limit=limit, context=context)            args += [('parent_id','!=',context['parent_company_id'])]        if name:            # Be sure name_search is symetric to name_get            name = name.split(' / ')[-1]            ids = self.search(cr, uid, [('name', operator, name)] + args, limit=limit, context=context)        else:            ids = self.search(cr, uid, args, limit=limit, context=context)                        ids = contact_ids + ids        if context.get('show_street_city',False):            return self.show_street_city(cr, uid, ids, context)        else:            return self.name_get(cr, uid, ids, context)        def name_get(self, cr, uid, ids, context=None):        if context is None:            context = {}        if isinstance(ids, (int, long)):            ids = [ids]        res = []        for record in self.browse(cr, uid, ids, context=context):            name = record.name#             if record.parent_id and not record.is_company:#                 name =  "%s, %s" % (record.parent_id.name, name)            if context.get('show_address'):                name = name + "\n" + self._display_address(cr, uid, record, without_company=True, context=context)                name = name.replace('\n\n','\n')                name = name.replace('\n\n','\n')            if context.get('show_email') and record.email:                name = "%s <%s>" % (name, record.email)            res.append((record.id, name))        return res        #Thanh: Redisplay Address    def _display_address(self, cr, uid, address, without_company=False, context=None):        '''        The purpose of this function is to build and return an address formatted accordingly to the        standards of the country where it belongs.        :param address: browse record of the res.partner to format        :returns: the address formatted in a display that fit its country habits (or the default ones            if not country is specified)        :rtype: string        '''        # get the information that will be injected into the display format        # get the address format#         address_format = "%(street)s, %(street2)s, %(city_name)s, %(state_name)s, %(zip_name)s, %(country_name)s"        address_format = "%(company_name)s / %(street)s / %(street2)s / %(city_name)s"        args = {            'city_name': address.city.name or '',            'zip_name': address.zip.name or '',            'state_code': address.state_id and address.state_id.code or '',            'state_name': address.state_id and address.state_id.name or '',            'country_code': address.country_id and address.country_id.code or '',            'country_name': address.country_id and address.country_id.name or '',            'company_name': address.parent_id and address.parent_id.name or '',        }        for field in self._address_fields(cr, uid, context=context):            args[field] = getattr(address, field) or ''#         if without_company:#             args['company_name'] = ''#         elif address.parent_id:#             #Thanh: No need to show compnay name# #             address_format = '%(company_name)s\n' + address_format#             address_format = address_format        return address_format % args    res_partner()class mail_mail(osv.Model):    _inherit = 'mail.mail'         def _get_default_mail_server_id(self, cr, uid, context=None):        this = self.pool.get('res.users').browse(cr, 1, uid, context=context)        ir_mail_server_id = False        if this.email:            ir_mail_server = self.pool.get('ir.mail_server')            ir_mail_server_ids = ir_mail_server.search(cr, 1, [('smtp_user','=',this.email)], order='sequence')            if ir_mail_server_ids:                ir_mail_server_id = ir_mail_server_ids[0]        return ir_mail_server_id         _defaults = {        'mail_server_id': lambda self, cr, uid, ctx=None: self._get_default_mail_server_id(cr, uid, ctx),    }mail_mail()# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
