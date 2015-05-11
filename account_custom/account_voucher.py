# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Comunitea All Rights Reserved
#    $Omar Castiñeira Saavedra <omar@comunitea.com>$
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

from openerp import models, api, fields


class AccountVoucher(models.Model):

    _inherit = "account.voucher"

    to_check = fields.Boolean("To check", help="Pending to check",
                              readonly=True)

    @api.multi
    def proforma_voucher(self):
        if self.env.user.to_check_payments:
            self.to_check = True

        return super(AccountVoucher, self).proforma_voucher()

    @api.multi
    def validate_voucher(self):
        self.to_check = False
