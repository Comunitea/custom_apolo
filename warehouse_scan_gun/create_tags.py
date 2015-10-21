# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015-2014 Comunitea Servicios Tecnológicos All Rights Reserved
#    $Kiko Sánchez$ <kiko@comunitea.com>
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
from openerp.exceptions import except_orm
from openerp.tools.translate import _


class create_tag_wizard(models.TransientModel):
    _inherit = "create.tag.wizard"


    @api.multi
    def print_from_gun(self, my_args):

        package_ids= my_args.get("package_ids", [])
        user_id = my_args.get("user_id", False)

        new_wzd = self.create()

        for package_id in package_ids:
            val = {'package_id' : package_id,
                   'wizard_id': new_wzd.id}
            res = new_wzd.write({'tag_ids': [(0,0, val)]})

        res = self.print_report()
        return res
