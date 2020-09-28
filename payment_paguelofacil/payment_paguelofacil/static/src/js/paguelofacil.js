odoo.define('payment_paguelofacil.paguelofacil', function (require) {
	"use strict";

	var ajax = require('web.ajax');
	var core = require('web.core');

	var _t = core._t;
	var QWeb = core.qweb;
	ajax.loadXML("/payment_paguelofacil/static/src/xml/paguelofacil.xml", QWeb);


	var formData = {
		'cclw' : $("input[name='cclw']").val(),
		'amount' : $("input[name='amount']").val(),
		'reference' : $("input[name='reference']").val(),
	}

	function get_form_event(){
		ajax.jsonRpc("/payment/paguelofacil/create_charge", 'call', {
			'cclw' : formData['cclw'],
			'reference' : formData['reference'],
			'amount' :  formData['amount']
		}).then(function(data){
			if ($.blockUI) { $.unblockUI(); }
			if(data.result == true){
				window.location.href = data.msg;
			}else if(data.result == false){
				errorDialog(data.msg);
			}
		}).guardedCatch(function(){
			if ($.blockUI) { $.unblockUI(); }
			errorDialog('An error occured. Please try again later or contact us.');
		});
	}


	function errorDialog(message){
		$('.modal').modal('hide');
		var wizard = $(QWeb.render('paguelofacil.error', {
			'msg': _t(message)
		}));
		var button = $(wizard.find("button"));
		button.on('click', function(){
			window.location.href = $("input[name='odoo_base_url']").val();
		});
		wizard.appendTo($('body')).modal({'keyboard': false, 'backdrop':'static'});
	}


	$.blockUI({
		'message': '<h2 class="text-white"><img src="/web/static/src/img/spin.png" class="fa-pulse"/>' +
			'    <br />' + "Porfavor espere..." +
			'</h2>'
	});
	get_form_event();
});
