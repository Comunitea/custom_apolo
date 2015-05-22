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


class res_partner(models.Model):

    _inherit = 'res.partner'

    channel_id = fields.Many2one('sale.channel', 'Sale channel')
    auto = fields.Boolean('Auto')

    @api.onchange('channel_id')
    def onchange_channel_id(self):
        if self.channel_id.pricelist_id:
            self.property_product_pricelist = self.channel_id.pricelist_id
            self.auto = True
        else:
            self.auto = False
