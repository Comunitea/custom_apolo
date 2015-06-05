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
from openerp import models, fields, api


class invoice_joint_promotion(models.TransientModel):

    _name = 'invoice.joint.promotion'
    date_start = fields.Date('Start', required=True)
    date_end = fields.Date('End', required=True)
    invoice_type = fields.Selection(
        (('draft', 'Draft'), ('proforma', 'pro-forma')),
        'Invoice type', default='draft', required=True)

    @api.multi
    def invoice(self):
        for promotion in self.env['sale.joint.promotion'].search(
                [('start_date', '<', self.date_end),
                 ('end_date', '>=', self.date_start),
                 ('id', 'in', self._context.get('active_ids', []))]):
            invoices = promotion.create_invoice(self.date_start, self.date_end)
            if invoices and self.invoice_type == 'proforma':
                invoices.signal_workflow('invoice_proforma2')
        return {'type': 'ir.actions.act_window_close'}
