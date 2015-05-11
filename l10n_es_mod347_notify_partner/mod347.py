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


class L10nEsAeatMod347PartnerRecord(models.Model):
    _name = 'l10n.es.aeat.mod347.partner_record'
    _inherit = ['l10n.es.aeat.mod347.partner_record', 'mail.thread']


class L10nEsAeatMod347Report(models.Model):
    _inherit = 'l10n.es.aeat.mod347.report'

    @api.multi
    def notify_partner(self):
        template_id = self.env.ref('l10n_es_mod347_notify_partner.email_template_347')
        for report in self:
            for line in report.partner_record_ids:
                if line.partner_id.email:
                    ctx = dict(self._context)
                    ctx.update({
                        'default_model': 'l10n.es.aeat.mod347.partner_record',
                        'default_res_id': line.id,
                        'default_use_template': bool(template_id),
                        'default_template_id': template_id.id,
                        'default_composition_mode': 'comment',
                        'mark_so_as_sent': True
                    })
                    composer_id = self.env['mail.compose.message'].with_context(
                        ctx).create({})
                    composer_id.with_context(ctx).send_mail()
