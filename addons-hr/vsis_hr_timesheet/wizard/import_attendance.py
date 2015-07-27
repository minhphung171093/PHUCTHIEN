# -*- encoding: utf-8 -*-
##############################################################################
#
#    General Solutions, Open Source Management Solution
#    Copyright (C) 2009 General Solutions (<http://gscom.vn>). All Rights Reserved
#
##############################################################################

import time

from osv import osv, fields

class import_attendance(osv.osv_memory):
    _name = 'import.attendance'
    _description = 'Timesheet from attendance'
    _columns = {
        'temp_usb': fields.boolean('Template from machine usb'),
        'temp_csv': fields.boolean('Template from csv file'),
    }

    _defaults = {
    }

    def confirm(self, cr, uid, ids, context=None):
        print 'testing.....'
        return {'type': 'ir.actions.act_window_close'}

import_attendance()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
