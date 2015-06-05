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


class InvoiceTourism(models.TransientModel):

    _name = 'invoice.tourism'

    date_start = fields.Date('Start', required=True)
    date_end = fields.Date('End', required=True)

    @api.multi
    def invoice(self):
        for tourism in self.env['sale.promotion.tourism'].search(
                [('id', 'in', self._context.get('active_ids', []))]):
            tourism.create_invoice(self.date_start, self.date_end)
        return {'type': 'ir.actions.act_window_close'}
