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


class sale_joint_promotion(models.Model):

    _inherit = 'sale.joint.promotion'

    type = fields.Selection((('discount', 'Discount'), ('rappel', 'Rappel')),
                            'Type', required=True)
    rappel_id = fields.Many2one('rappel', 'Rappel')

    @api.multi
    def get_rappel_amount(self, date_start, date_end):
        calculated = self.env['rappel.calculated'].read_group(
            [('rappel_id', '=', self.rappel_id.id),
             ('period_start', '>=', date_start),
             ('period_end', '<=', date_end), ('invoiced', '=', True)],
            ['rappel_id', 'quantity'], ['rappel_id'], limit=1)
        if not calculated:
            return 0
        return {self.rappel_id.type_id.product_id.id:
                calculated[0]['quantity'] * (self.discount_assumed / 100)}

    @api.multi
    def get_amount(self, date_start, date_end):
        res = super(sale_joint_promotion, self).get_amount(date_start,
                                                           date_end)
        if self.rappel_id:
            return self.get_rappel_amount(date_start, date_end)
        return res
