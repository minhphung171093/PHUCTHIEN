# -*- encoding: utf-8 -*-
##############################################################################
#
#
##############################################################################
{
	"name" : "General Payroll",
	"version" : "7.0",
	'author': 'Le Truong Thanh <thanh.lt1689@gmail.com>',
    'category': 'General 70',
	"description" : """
	""",
	"depends" : ["hr_payroll","hr_overtime","general_hr_holidays","general_hr_contract","general_hr_contract_trial"],
	"demo_xml" : [],
	"update_xml" : [
		'security/hr_security.xml',
		'security/ir.model.access.csv',
		
 		'hr_overtime_data.xml',
		
		'hr_advance_payment_view.xml',
		'hr_insurance_book_view.xml',
		'hr_overtime_view.xml',
		
		'hr_contract_view.xml',
		'hr_contract_trial_view.xml',
		'hr_payroll_view.xml',
		'hr_employee_view.xml',
		
 		'data/hr_payroll_data.xml',
	],
	"active": False,
	"installable": True,

}
