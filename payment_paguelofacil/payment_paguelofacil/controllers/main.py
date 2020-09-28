# -*- coding: utf-8 -*-
import werkzeug
import logging

from odoo import http
from odoo.http import request
from odoo.exceptions import ValidationError, UserError
from odoo.addons.payment.controllers.portal import PaymentProcessing, WebsitePayment

_logger = logging.getLogger(__name__)


class PagueloFacilController(http.Controller):


	@http.route(['/payment/paguelofacil/return'], type='http', auth='none', csrf=False, methods=['GET'])
	def paguelofacil_form_feedback(self, **kw):
		if not kw.get('Estado'):
			raise werkzeug.exceptions.NotFound()
		_logger.info(kw)
		request.env['payment.transaction'].sudo().form_feedback(kw, 'paguelofacil')
		return werkzeug.utils.redirect('/payment/process')



	@http.route(['/payment/paguelofacil/create_charge'], type='json', auth='public')
	def paguelofacil_create_charge(self, **kwargs):
		try:
			TX = request.env['payment.transaction']
			tx = None
			if kwargs.get('reference'):
				tx = TX.sudo().search([('reference', '=', kwargs['reference'])])
			if not tx:
				tx_id = (request.session.get('sale_transaction_id') or
						request.session.get('website_payment_tx_id'))
				tx = TX.sudo().browse(int(tx_id))
			if not tx:
				raise werkzeug.exceptions.NotFound()
			return tx._create_paguelofacil_charge(kwargs)
		except Exception as __ERROR:
			return {
				'result': False,
				'msg': __ERROR
			}