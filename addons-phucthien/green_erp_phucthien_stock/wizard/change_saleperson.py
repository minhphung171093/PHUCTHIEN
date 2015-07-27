# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
import time

from openerp.osv import fields, osv
from openerp import netsvc
from openerp import pooler
from openerp.osv.orm import browse_record, browse_null
from openerp.tools.translate import _

class change_saleperson(osv.osv_memory):
    _name = "change.saleperson"
    _description = "Change Sale Person all"
    
    _columns = {
        'saleperson_id':fields.many2one('res.users', 'Nhân viên kinh doanh thay đổi',required=True),
        }

    def run_change(self, cr, uid, ids, context=None):      
        dulieu_donghang_pool = self.pool.get('dulieu.donghang')
        for change_saleperson in self.browse(cr,uid,ids):
            sequence_obj = self.pool.get('ir.sequence')
            for line in context.get('active_ids',[]):                   
                dulieu_donghang = dulieu_donghang_pool.browse(cr, uid, line, context=context)
                dulieu_donghang_pool.write(cr, uid, [line],{'saleperson_id':change_saleperson.saleperson_id.id}, context=context)
        return True
               

change_saleperson()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
