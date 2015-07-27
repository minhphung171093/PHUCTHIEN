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

{
    'name': 'General Hr Expense',
    'version': '1.1',
    'author': 'Phạm Tuấn Kiệt <tykiet.208@gmail.com>',
    'category': 'General 70',
    'sequence': 21,
    'website': '',
    'summary': 'Employees Expense Management',
    'description': """
    """,
    'depends': ['general_hr','hr_expense','general_hr_account','report_aeroo'],
    'data': [
             'security/general_hr_expense_security.xml',
             'security/ir.model.access.csv',
             
             'wizard/hr_expense_paid.xml',

             'hr_expense_workflow.xml',
             'email_template.xml',
             'hr_expense_view.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
