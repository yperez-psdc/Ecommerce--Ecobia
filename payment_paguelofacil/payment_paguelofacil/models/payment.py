# -*- coding: utf-8 -*-

import requests
import re
import hashlib
import uuid
import json
#import base64
import urllib.parse
from odoo.http import request
from odoo import models, fields, api, _, exceptions
from odoo.addons.payment.models.payment_acquirer import ValidationError
from odoo.tools.float_utils import float_compare, float_repr, float_round

import logging
_logger = logging.getLogger(__name__)


EXCEPCIONES_600 = [
	{'code': 600, 'msg': 'Solicite nuevamente el CCLW y verifique los datos, comuniquese con soporte con los datos de su comercio.'},
	{'code': 601, 'msg': 'Su comercio ha sido desactivado por falta de procesamiento solicite la reactivación.'},
	{'code': 602, 'msg': 'Verifique que los valores de cada parámetro de entrada coincide exactamente con los proporcionados en esta documentación.'},
	{'code': 603, 'msg': 'El monto de la transacción mínimo es $ 1.00.'},
	{'code': 604, 'msg': 'El monto máximo de transacción permitido a su comercio es menor al monto.'},
	{'code': 605, 'msg': 'Número de tarjeta no valido.'},
	{'code': 606, 'msg': 'Número de código de verioficación no válido.'},
	{'code': 607, 'msg': 'Número de tarjeta no valido.'},
	{'code': 608, 'msg': 'Formato de email no valido.'},
	{'code': 609, 'msg': 'Nombre demasiado corto o largo.'},
	{'code': 610, 'msg': 'Apellido demasiado corto o largo.'},
	{'code': 611, 'msg': 'Número de telefono no valido.'},
	{'code': 612, 'msg': 'Al realizar 3 transacciones con la misma tarjeta y datos de procesamiento el sistema detecta que es posiblemente una transacción duplicada y solo permite hasta 3 intentos.'},
	{'code': 613, 'msg': 'Su límite mensual fue alcanzado. Solicite un aumento de límites.'},
	{'code': 614, 'msg': 'Su límite diario fue alcanzado. Solicite un aumento de límites.'},
	{'code': 615, 'msg': 'Su cuenta ha sido suspendida por el banco, por favor comuniquese con nostros para mayor información.'},
	{'code': 616, 'msg': 'Este emailPago ya fue pagado.'},
	{'code': 617, 'msg': 'Este emailPago ya caducó.'}
]


class PagueloFacilPaymentAcquirer(models.Model):
	_inherit = "payment.acquirer"

	provider = fields.Selection(
		selection_add=[('paguelofacil', 'Paguelo Facil')]
	)
	paguelofacil_cclw = fields.Char(
		required_if_provider="paguelofacil",
		string="CCLW", groups="base.group_user", help=""
	)

	def _get_paguelofacil_urls(self, environment):
		"""Para este metodo usamos la propiedad environment a pesar que la
		propiedad ya no existe en la version 13.
		"""

		if environment == 'prod':
			return {
				'paguelofacil_form_url': 'https://secure.paguelofacil.com',
			}
		else:
			return {
				'paguelofacil_form_url':'https://sandbox.paguelofacil.com',
			}

	def _get_paguelofacil_form_url(self):
		environment = 'prod' if self.state == 'enabled' else 'test'
		return self._get_paguelofacil_urls(environment)['paguelofacil_form_url']

	def paguelofacil_form_generate_values(self, values):
		self.ensure_one()
		base_url = self.env['ir.config_parameter'].get_param('web.base.url')
		paguelofacil_tx_values = dict(values)
		temp_paguelofacil_tx_values = {
			'cclw':self.paguelofacil_cclw,
			'odoo_base_url': base_url
		}
		paguelofacil_tx_values.update(temp_paguelofacil_tx_values)
		return paguelofacil_tx_values

	def paguelofacil_get_form_action_url(self):
		self.ensure_one()
		return ''


class PagueloFacilPaymentTransaction(models.Model):
	_inherit = 'payment.transaction'

	pf_type = fields.Char(string="PF Type", groups='base.group_user')
	pf_date = fields.Date(string="PF Date", groups='base.group_user')
	pf_cmtn = fields.Float(string="PF CMTN", groups='base.group_user')
	pf_cdsc = fields.Char(string="PF CDSC", groups='base.group_user')
	pf_total_paid = fields.Float(string="PF Total Paid", groups='base.group_user')
	pf_user = fields.Char(string="PF User", groups='base.group_user')
	pf_email = fields.Char(string="PF Email", groups='base.group_user')
	pf_deal = fields.Char(string="PF Deal", groups='base.group_user')

	def _create_paguelofacil_charge(self, data):
		try:
			paguelofacil_url = self.acquirer_id._get_paguelofacil_form_url()
			cclw = self.acquirer_id.paguelofacil_cclw
			cmtn = self.amount
			cdsc = self.reference

			# Enviamos la ruta de retorno
			base_url = self.env['ir.config_parameter'].get_param('web.base.url')
			return_url = '%s/payment/paguelofacil/return' % (base_url)
			return_url = urllib.parse.quote(return_url, safe='')

			ref_url = "%s/LinkDeamon.cfm?CCLW=%s&CMTN=%s&CDSC=%s&RETURN_URL=%s" % \
				(paguelofacil_url, cclw, cmtn, cdsc, return_url)
			return {
				'result': True,
				'msg': ref_url
			}
		except Exception as __ERROR:
			return {
				'result': False,
				'msg': __ERROR
			}

	def _paguelofacil_form_get_tx_from_data(self, data):
		reference = data.get('CDSC')

		if not reference:
			error_msg = _('PagueloFacil: received data with missing reference (%s)') % (reference)
			_logger.info(error_msg)
			raise ValidationError(error_msg)

		tx = self.search([('reference', '=', reference)])
		if not tx or len(tx) > 1:
			error_msg = 'PagueloFacil: received data for reference %s' % (reference)
			if not tx:
				error_msg += '; no order found'
			else:
				error_msg += '; multiple order found'
			_logger.info(error_msg)
			raise ValidationError(error_msg)
		return tx[0]

	def _paguelofacil_form_get_invalid_parameters(self, data):
		invalid_parameters = []
		return invalid_parameters

	def _paguelofacil_form_validate(self, data):
		if self.state != 'draft':
			logging.info('PagueloFacil: trying to validate an already validated tx (ref %s)', self.reference)
			return True

		if data.get('Estado') == 'Aprobada':
			self.write({
				'date': fields.datetime.now(),
				'acquirer_reference': data.get('Oper'),
				'pf_type': data.get('Tipo'),
				'pf_cmtn': data.get('CMTN'),
				'pf_cdsc': data.get('CDSC'),
				'pf_user': data.get('Usuario'),
				'pf_email': data.get('Email'),
				'pf_total_paid': data.get('TotalPagado'),
				'pf_deal': data.get('Deal')
			})
			self._set_transaction_done()
			self.execute_callback()
			return True
		else:
			self.write({
				'date': fields.datetime.now(),
				'state_message': data.get('Razon'),
				'pf_type': data.get('Tipo'),
				'pf_cmtn': data.get('CMTN'),
				'pf_cdsc': data.get('CDSC'),
				'pf_user': data.get('Usuario'),
				'pf_email': data.get('Email'),
				'pf_total_paid': data.get('TotalPagado'),
				'pf_deal': data.get('Deal')
			})
			self._set_transaction_cancel()
			return False