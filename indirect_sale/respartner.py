# -*- coding: utf-8 -*-
##############################################################################
#
#    Carlos Lombardía Rodríguez Copyright Comunitea SL 2015
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
from openerp import models, fields, api


class partner_supplier_rel(models.Model):

    _inherit = 'res.partner'

    supplier_ids = fields.Many2many('res.partner', 'partner_supplier_rel',
                                    'partner_id','supplier_id',
                                    string='Suppliers',
                                    domain=[('supplier', '=', True)])
    customer_ids = fields.Many2many('res.partner', 'partner_supplier_rel',
                                    'supplier_id','partner_id',
                                    string='Customers',
                                    domain=[('customer', '=', True)])
    indirect_customer = fields.Boolean("Indirect customer")
    supplier_seq_id = fields.Many2one('ir.sequence', 'Supplier sequence')