# -*- coding: utf-8 -*-
##############################################################################
#
#    Omar Castiñeira Saavedra Copyright Comunitea SL 2015
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

from openerp import models, fields, api, exceptions, _


class ResPartner(models.Model):

    _inherit = "res.partner"

    unilever_code = fields.Char("Unilever code", size=10)
    favorite = fields.Boolean('Favorite')
    high_competition = fields.Boolean('High competition')
    close_days = fields.Many2many('week.days', 'partner_close_week_days',
                                  'partner_id', 'close_days_id',
                                  'Closure days')
    morning_open_time = fields.Float('Morning open time')
    morning_close_time = fields.Float('Morning close time')
    afternoon_open_time = fields.Float('Afternoon open time')
    afternoon_close_time = fields.Float('Afternoon close time')
    from_competence_id = fields.Many2one("res.partner.competence",
                                         "From Competence",
                                         help="Origin competitor of customer")
    to_competence_id = fields.Many2one("res.partner.competence",
                                       "To Competence",
                                       help="New competitor of customer")
    local_share_partner_id = fields.Many2one('res.partner',
                                             'Partner local share')
    indirect_customer = fields.Boolean("Indirect customer")

    _constraints = [(models.Model._check_recursion,
                    'You cannot create recursive Partner hierarchies.',
                    ['local_share_partner_id'])]

    @api.multi
    def act_active(self):
        res = super(ResPartner, self).act_active()
        sync_obj = self.env["res.partner.sync"]
        for partner in self:
            if partner.customer and partner.is_company and \
                    not partner.indirect_customer:
                if not partner.ref:
                    raise exceptions.Warning(_("Please set a reference to "
                                               "partner %s") % partner.name)
                sync_obj.register_partner_op(partner.id, 'A')
        return res

    @api.multi
    def register_again(self):
        res = super(ResPartner, self).register_again()
        sync_obj = self.env["res.partner.sync"]
        for partner in self:
            if partner.customer and partner.is_company and \
                    not partner.indirect_customer:
                if not partner.ref:
                    raise exceptions.Warning(_("Please set a reference to "
                                               "partner %s") % partner.name)
                sync_obj.register_partner_op(partner.id, 'A')
        return res

    @api.multi
    def unlink(self):
        for partner in self:
            if partner.customer and partner.state2 == "registered":
                raise exceptions.Warning(_("Cannot delete partener %s because "
                                           "is registered, please unregister "
                                           "it") % partner.name)
        return super(ResPartner, self).unlink()

    @api.multi
    def write(self, vals):
        res = super(ResPartner, self).write(vals)
        sync_obj = self.env["res.partner.sync"]
        for partner in self:
            if partner.customer and partner.state2 == "registered" and \
                    partner.is_company and not partner.indirect_customer:
                sync_obj.register_partner_op(partner.id, 'M')

        return res


class ProcessUnregisterPartner(models.TransientModel):

    _inherit = "process.unregister.partner"

    @api.multi
    def unregister_partner(self):
        res = super(ProcessUnregisterPartner, self).unregister_partner()
        partner_ids = self.env.context['active_ids']
        partner_obj = self.env["res.partner"]
        sync_obj = self.env["res.partner.sync"]
        for partner in partner_obj.browse(partner_ids):
            if partner.customer and partner.is_company and \
                    not partner.indirect_customer:
                if not partner.ref:
                    raise exceptions.Warning(_("Please set a reference to "
                                               "partner %s") % partner.name)
                sync_obj.register_partner_op(partner.id, 'B')
        return res
