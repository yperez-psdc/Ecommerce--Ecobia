# -*- coding: utf-8 -*-
{
	'name': "PagueloFacil Payment Acquirer",
	'summary': """
		Implementation PagueloFacil""",
	'description': """
		PagueloFacil Payment Acquirer.
	""",

	'author': "PSDC INNOVA",

	'category': 'Accounting/Payment',
    'images': ['static/description/icon.png'],
	'version': '13.0.1.0.2',

	'depends': ['payment'],

	# any external dependence necessary for this one to work correctly
	'external_dependencies':{
		'python':[],
		'bin':[]
	},

	# always loaded
	'data': [
		'views/payment_view.xml',
		'views/paguelofacil_template.xml',
		'data/payment_acquirer_data.xml',
	],

	'qweb': [
		'/payment_paguelofacil/static/src/xml/paguelofacil.xml'
	],

	'demo': [
		#'demo/demo.xml',
	],
	'post_init_hook': 'create_missing_journal_for_acquirers',
}
