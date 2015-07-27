# -*- encoding: utf-8 -*-
##############################################################################
#
#    Viet Solution Infomation System, Open Source Management Solution
#    Copyright (C) 2009 General Solutions (<http://www.vietsolutionis.com>). All Rights Reserved
#
##############################################################################


{
    "name" : "VSIS HR",
    'version': '1.0',
    "category" : "VSIS Modules",
    'summary': 'MKP Timesheets',
    "author" : "Viet Solution Infomation System",
    "website" : "http://www.vietsolutionis.com",
    "description" : """VSIS HR""",
    'images': [],
    'depends': ["hr", 'hr_attendance', 'hr_holidays', 'hr_timesheet', 'hr_timesheet_invoice', 'hr_timesheet_sheet'],
    'data': [
        'hr_timesheet_sheet_data.xml',
        'wizard/timesheet_from_attendance_view.xml',
        'wizard/import_attendance_view.xml',
        'hr_attendance_view.xml',
        'hr_timesheet_sheet_view.xml',
    ],
    'demo': [],
    'test':[],
    'installable': True,
    'auto_install': False,
    #'js': ['static/src/js/timesheet.js',],
    'qweb': ['static/src/xml/timesheet.xml',],
    'css': ['static/src/css/timesheet.css',],
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
