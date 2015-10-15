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
from datetime import date, timedelta


class SaleExportEdi(models.Model):

    _name = 'sale.export.edi'

    user_id = fields.Many2one("res.users", "User", readonly=True,
                              required=True,
                              default=lambda self: self.env.user)
    date = fields.Date("Date", default=fields.Date.today(), required=True)
    state = fields.Selection((('pending', 'Pending'), ('send', 'Send')),
                             'State', default='pending')
    period_start = fields.Date('Period start', required=True)
    period_end = fields.Date('Period end', required=True)

    @api.model
    def _get_this_week(self):
        today = date.today()
        weekday = today.weekday()
        monday = today + timedelta(days=-weekday)
        sunday = monday + timedelta(days=6)
        return monday, sunday

    @api.model
    def generate_week(self):
        monday, sunday = self._get_this_week()
        self.create({
            'period_start': monday,
            'period_end': sunday,
        })
