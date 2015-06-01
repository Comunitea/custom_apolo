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

import os
import unicodecsv
import logging
import shutil
from datetime import datetime
from openerp import models, api, exceptions, _

_logger = logging.getLogger(__name__)


class AccountIntegrateWzd(models.TransientModel):

    _name = "accout.integrate.wzd"

    @api.model
    def import_files(self):
        config_obj = self.env["ir.config_parameter"]
        period_obj = self.env["account.period"]
        jounal_obj = self.env["account.journal"]
        acc_move_obj = self.env["account.move"]
        account_obj = self.env["account.account"]
        partner_obj = self.env["res.partner"]
        analytic_acc_obj = self.env["account.analytic.account"]
        move_line_obj = self.env["account.move.line"]
        param = config_obj.search([('key', '=', 'integrate.accounting.path')])
        if not param:
            raise exceptions.UserError(_("You must define the system parameter"
                                         " integrate.accounting.path with the "
                                         "path of accounting files"))
        path = param[0].value
        files = [s for s in os.listdir(path)
                 if os.path.isfile(os.path.join(path, s))]
        files = [os.path.join(path, f) for f in files]
        files.sort(key=lambda x: os.path.getmtime(x))
        for file_name in files:
            extension = file_name.split(".")[-1]
            if extension not in ["CSV", "csv"]:
                continue

            last_move = False
            last_date = False
            last_period_id = False
            last_move_id = False
            posted = False
            analytic_account = False
            error = False
            journal_id = jounal_obj.search([('name', '=',
                                             u"Diario Importación")])
            if not journal_id:
                _logger.error(_(u"%s: Please, create an account journal "
                                u"with name 'Diario Importación'.") %
                              file_name)
                continue
            journal_id.ensure_one()
            _logger.info(_(u"%s: Processing.") % file_name)
            data_file = open(file_name, 'r')
            data_file.seek(0)
            reader = unicodecsv.DictReader(data_file, delimiter=';',
                                           encoding='ISO-8859-1')
            for row in reader:
                try:
                    if row.get('Sit', False) == 'T':
                        error = True
                        break
                    if not row.get('Referencia', False) or not \
                            row.get('Cuenta', False):
                        continue

                    if row['Fecha'] != last_date:
                        last_date = datetime.\
                            strftime(datetime.strptime(row['Fecha'],
                                                       "%d-%m-%Y"), "%Y-%m-%d")
                        ctx = dict(self.env.context)
                        if row['Concepto'] in ('APERTURA', 'CIERRE', 'PYG',
                                               'EXPLOTACIO'):
                            ctx['account_period_prefer_normal'] = False

                        last_period_id = period_obj.with_context(ctx).\
                            find(last_date)[0]

                    if int(row['Referencia']) != last_move:
                        if last_move_id and not posted:
                            last_move_id.post()
                            analytic_account = False
                        last_move = int(row['Referencia'])
                        move_ids = acc_move_obj.search([('name', '=',
                                                         str(last_move)),
                                                        ('date', '=',
                                                         last_date),
                                                        ('journal_id', '=',
                                                         journal_id.id)])
                        if move_ids:
                            move_ids[0].button_cancel()
                            move_ids[0].unlink()
                        if row.get('Sit', False) == 'B':
                            posted = True
                            continue
                        move_vals = {
                            'ref': row['Concepto'],
                            'journal_id': journal_id.id,
                            'period_id': last_period_id.id,
                            'date': last_date,
                            'name': str(last_move)
                        }
                        last_move_id = acc_move_obj.create(move_vals)
                        posted = False
                    elif posted:
                        continue

                    ref = row.get('Documento', "")
                    if not ref:
                        ref = row.get('Ampliacion', "")
                    elif row.get('Ampliacion'):
                        ref += u" // " + row['Ampliacion']
                    account_ids = account_obj.search([('code', '=',
                                                       row['Cuenta'])])
                    if (row['Cuenta'].startswith('430') or row['Cuenta'].
                            startswith('410') or row['Cuenta'].
                            startswith('400') or row['Cuenta'].
                            startswith('440')) and not account_ids:
                        partner_ref = row['Cuenta'][3:]
                        partner_ref = int(partner_ref) and \
                            str(int(partner_ref)) or False
                    else:
                        partner_ref = False

                    if partner_ref:
                        partner_ids = partner_obj.search([("ref", '=',
                                                           partner_ref), '|',
                                                          ('active', '=',
                                                           True), ('active',
                                                                   '=',
                                                                   False)])
                        if not partner_ids:
                            partner_vals = {
                                "customer": row['Cuenta'].startswith('43')
                                and True or False,
                                "ref": partner_ref,
                                "name": row['Titulo'] + u" (IMPORTADO)",
                                "supplier": row['Cuenta'].startswith('43')
                                and False or True,
                                "is_company": True
                            }
                            partner = partner_obj.create(partner_vals)
                            partner_ids = [partner]
                    else:
                        partner_ids = []
                    if partner_ids:
                        account_code = row['Cuenta'][:3].ljust(9, '0')
                    else:
                        account_code = row['Cuenta']
                    account_ids = account_obj.search([('code', '=',
                                                       account_code)])
                    if not account_ids:
                        _logger.info(_("%s: There isn't any account created "
                                       "with code %s" % (file_name,
                                                         account_code)))
                        parent_ids = False
                        parent_account_code = account_code[:-1]
                        while len(parent_account_code) > 0:
                            parent_ids = account_obj.\
                                search([('code', '=', parent_account_code)])
                            if parent_ids:
                                parent_account_code = ""
                            parent_account_code = parent_account_code[:-1]
                        if parent_ids:
                            parent_ut = parent_ids[0].user_type.id
                            account_id = account_obj.\
                                create({'code': account_code,
                                        'name': row['Titulo'],
                                        'type': "other",
                                        'user_type': parent_ut,
                                        'parent_id': parent_ids[0].id})
                            account_ids = [account_id]
                        else:
                            _logger.error(_("%s: Cannot create account with "
                                            "code %s.") % (file_name,
                                                           account_code))
                            error = True
                            break

                    debit = 0.0
                    credit = 0.0
                    if row.get('Debe', False):
                        debit_t = float(row['Debe'].replace(",", "."))
                        if debit_t < 0:
                            credit = abs(debit_t)
                        else:
                            debit = debit_t
                    if row.get('Haber', False):
                        credit_t = float(row['Haber'].replace(",", "."))
                        if credit_t < 0:
                            debit = abs(credit_t)
                        else:
                            credit = credit_t

                    move_line_vals = {
                        'journal_id': journal_id.id,
                        'period_id': last_period_id.id,
                        'name': row['Concepto'],
                        'ref': ref,
                        'date': last_date,
                        'debit': debit,
                        'credit': credit,
                        'partner_id': partner_ids and partner_ids[0].id
                        or False,
                        'account_id': account_ids[0].id,
                        'move_id': last_move_id.id
                    }
                    if row.get('Obsv'):
                        analytic_code = row['Obsv'].replace("-", "")
                        analytic_acc_id = analytic_acc_obj.\
                            search([('code', '=', analytic_code)])
                        if analytic_acc_id:
                            analytic_account = analytic_acc_id[0]
                            if account_code.startswith('7') or \
                                    account_code.startswith('6'):
                                move_line_vals['analytic_account_id'] = \
                                    analytic_account.id
                        else:
                            _logger.warning(_("%s: Any analytic account with "
                                              "code %s") %
                                            (file_name, analytic_code))
                    elif analytic_account:
                        if account_code.startswith('7') or \
                                account_code.startswith('6'):
                            move_line_vals['analytic_account_id'] = \
                                analytic_account.id

                    move_line_obj.create(move_line_vals)

                except Exception, e:
                    _logger.error(_("%s: Exception %s in row %s") %
                                  (file_name, e, row))
                    error = True
                    break

            if not error:
                if last_move_id:
                    last_move_id.post()
                backup_path = path + os.sep + "processed"
                if not os.path.exists(backup_path):
                    os.mkdir(backup_path)
                src_file = file_name
                dst_file = backup_path + os.sep + file_name.split(os.sep)[-1]
                shutil.move(src_file, dst_file)
                #shutil.rmtree(src_file)
