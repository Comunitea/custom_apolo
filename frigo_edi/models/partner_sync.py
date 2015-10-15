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

from openerp import models, fields, api


class ResPartnerSync(models.Model):

    _name = "res.partner.sync"

    @api.one
    def _get_closure_days(self):
        days = [" ", " ", " ", " ", " ", " ", " "]
        if self.partner_id.close_days:
            for day in self.partner_id.close_days:
                days[day.sequence - 1] = "F"
        self.close_days = "".join(days)

    @api.one
    def _get_timetable(self):
        res = ""
        for x in ["morning_open_time", "morning_close_time",
                  "afternoon_open_time", "afternoon_close_time"]:
            if eval("p.x", p=self.partner_id, x=x):
                t = eval("p.x", p=self.partner_id, x=x)
                res += "%02d:%02d" % (int(t), round((t % 1) * 60))
            else:
                res += "00:00"
        self.timetable_str = res

    @api.one
    def _get_contact_str(self):
        res = ""
        contacts = [x for x in self.partner_id.child_ids if not x.is_company]
        limit = 3
        cont = 0
        while (cont < limit):
            if contacts and len(contacts) > cont:
                res += contacts[cont].function and contacts[cont].\
                    function[:15].ljust(15, " ") or "".ljust(15, " ")
                res += contacts[cont].name[:30].ljust(30, " ")
                res += contacts[cont].email and contacts[cont].\
                    email[:50].ljust(50, " ") or "".ljust(50, " ")
                res += contacts[cont].phone and contacts[cont].\
                    phone[:15].ljust(15, " ") or "".ljust(15, " ")
                res+= "".ljust(16, " ")
            else:
                res+= "".ljust(126, " ")
            cont += 1
        self.contact_str = res

    state = fields.Selection([('pending', 'Pending'),
                              ('sync', 'Synchronized')], "State",
                              readonly=True, default="pending")
    partner_id = fields.Many2one("res.partner", "Partner", required=True)
    operation_type = fields.Selection([('A', 'New'), ('B', 'Delete'),
                                       ('M', 'Update')], 'Operation type',
                                      readonly=True, default="A",
                                      required=True)
    user_id = fields.Many2one("res.users", "User", readonly=True,
                              required=True,
                              default=lambda self: self.env.user)
    date = fields.Date("Date", default=fields.Date.today(), required=True)
    close_days = fields.Char("Closure days", compute='_get_closure_days',
                             readonly=True)
    timetable_str = fields.Char("Timetable", compue='_get_timetable',
                                readonly=True)
    contact_str = fields.Char("Contacts str.", readonly=True,
                              compute="_get_contact_str")

    @api.model
    def register_partner_op(self, partner_id, opt_type):
        exists_obj = self.search([("state", "=", "pending"),
                                  ("partner_id", "=", partner_id),
                                  ('operation_type', '=', opt_type)])
        if exists_obj:
            exists_obj.write({'date': fields.Date.today(),
                              'user_id': self.env.user.id})
        else:
            self.create({'partner_id': partner_id,
                         'operation_type': opt_type})

