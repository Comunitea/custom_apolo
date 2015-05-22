# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Comunitea All Rights Reserved
#    $Jesús Ventosinos Mayor <jesus@comunitea.com>$
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
from openerp import models, fields, api, exceptions, _


class ProductTemplate(models.Model):

    _inherit = 'product.template'

    channel_ids = fields.Many2many('sale.channel', 'product_sale_channel_rel',
                                   'product_id', 'channel_id', 'Channels')


class ProductProduct(models.Model):

    _inherit = 'product.product'

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        pricelist_id = self._context.get('pricelist', False)
        if pricelist_id:
            channel = self.env['sale.channel'].search([('pricelist_id', '=',
                                                        pricelist_id)])
            if channel:
                product_ids = channel.with_context({}).mapped('product_ids.product_variant_ids')
                args.append(('id', 'in', product_ids._ids))
        return super(ProductProduct, self).name_search(name, args= args,
                                                       operator=operator,
                                                       limit=limit)
