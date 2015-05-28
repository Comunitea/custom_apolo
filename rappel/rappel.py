# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2004-2014 Pexego Sistemas Informáticos All Rights Reserved
#    $Marta Vázquez Rodríguez$ <marta@pexego.es>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
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
from openerp import models, fields, _, api, exceptions


class rappel(models.Model):
    _name = "rappel"
    _description = 'Rappel Model'
    PERIODICITIES = [('monthly', 'Monthly'), ('quarterly', 'Quarterly'),
                     ('semiannual', 'Semiannual'), ('annual', 'Annual')]
    CALC_MODE = [('fixed', 'Fixed'), ('variable', 'Variable')]
    CALC_AMOUNT = [('percent', 'Percent'), ('qty', 'Quantity')]
    CALC_TYPE = [('monetary', 'value'), ('qty', 'Quantity')]

    name = fields.Char('Concept', required=True)
    type_id = fields.Many2one('rappel.type', 'Type', required=True)
    date_start = fields.Date('Date Start', required=True)
    date_stop = fields.Date('Date Stop')
    last_use = fields.Date('Last use of the rappel')
    periodicity = fields.Selection(PERIODICITIES,
                                   'Periodicity',
                                   required=True)
    calc_mode = fields.Selection(CALC_MODE, 'Fixed/Variable')
    fix_qty = fields.Float('Fix')
    sections = fields.One2many('rappel.section', 'rappel_id', 'Sections')
    global_application = fields.Boolean('Global', default=True)
    product_id = fields.Many2one('product.product', 'Product')
    product_categ_id = fields.Many2one('product.category', 'Category')
    rappel_group_id = fields.Many2one('product.rappel.group', 'Rappel group')
    calc_amount = fields.Selection(CALC_AMOUNT, 'Percent/Quantity')
    calc_type = fields.Selection(CALC_TYPE, 'value/quantity')
    uom_id = fields.Many2one('product.uom', 'UoM')
    last_execution = fields.Date('Last execution')
    import_discount = fields.Float('Import Discounted', readonly=True,
                                   compute='_get_total_discounted')
    customer_ids = fields.Many2many('res.partner', 'rappel_customer_rel_',
                                    'rappel_id', 'customer_id', 'Customers')

    @api.multi
    def _get_total_discounted(self):
        for rappel in self:
            total = 0.0
            for calculated in rappel.calculated_ids:
                total += calculated.total_import
            rappel.import_discount = total

    @api.model
    def create(self, vals):
        if vals.get('global_application', False) is False:
            if not vals.get('product_id', False) and not \
                    vals.get('product_categ_id', False) and not \
                    vals.get('rappel_group_id', False):
                raise exceptions.Warning(_('Error'),
                                         _('Product and category are empty'))
        return super(rappel, self).create(vals)

    @api.multi
    def write(self, vals):
        res = super(rappel, self).write(vals)
        keys = vals.keys()
        if 'global_application' in keys or 'product_id' in keys or \
                'product_categ_id' in keys:
            for rappel_o in self:
                if rappel_o['global_application'] is False:
                    if not rappel_o['product_id'] and not \
                            rappel_o['product_categ_id'] and not \
                            rappel_o['rappel_group_id']:
                        raise exceptions.Warning(_('Error'),
                                                 _(' Product and category are \
empty'))
        return res

    @api.multi
    def get_products(self):

        product_obj = self.env['product.template']
        prod_sup_obj = self.env['product.supplierinfo']
        product_ids = []
        for rappel in self:
            if not rappel.global_application:
                if rappel.product_categ_id:
                    product_ids = product_obj.search(
                        [('categ_id', '=', rappel.product_categ_id.id)])._ids
                elif rappel.rappel_group_id:
                    product_ids = product_obj.search(
                        [('rappel_group_id', '=',
                          rappel.rappel_group_id.id)])._ids
                elif rappel.product_id:
                    product_ids = [rappel.product_id.id]
            else:
                product_ids = product_obj.search([])._ids
        return product_ids

    @api.multi
    def get_partners(self):
        partners = self.customer_ids
        for customer in self.customer_ids:
            for child in customer.child_ids:
                partners += child
        return partners


class rappel_section(models.Model):
    _name = "rappel.section"
    _description = "Rappel section model"

    rappel_from = fields.Float('From')
    rappel_until = fields.Float('Until')
    percent = fields.Float('Value')
    rappel_id = fields.Many2one('rappel', 'Rappel')


class rappel_calculation(models.Model):

    _name = 'rappel.calculated'

    rappel_id = fields.Many2one('rappel', 'Rappel', required=True)
    customer_id = fields.Many2one('res.partner', 'Customer', required=True)
    period = fields.Char('Period', required=True)
    quantity = fields.Float('Quantity', required=True)
    invoiced = fields.Boolean('Invoiced')
    invoice_id = fields.Many2one('account.invoice', 'Invoice')
