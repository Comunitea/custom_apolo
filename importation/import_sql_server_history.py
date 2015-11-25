# -*- coding: utf-8 -*-

import sys
import xmlrpclib
import socket
import pyodbc
import traceback
import time

UOM_MAP = {"K": "kg",
           "U": "Unit(s)",
           "C": "Box(es)",
           "L": "Liter(s)"}

TYPE_MAP = {"S": "service",
            "L": "product",
            "N": "consu"}

IVA_MAP = {
    "1": ["S_IVA10B", "P_IVA10_BC"],
    "2": ["S_IVA4B", "P_IVA4_BC"],
    "3": ["S_IVA21B", "P_IVA21_BC"],
    "4": ["S_IVA0", "P_IVA0_BC"]
}

IVAA_MAP = {
    "10": ["S_IVA10B", "P_IVA10_BC"],
    "4": ["S_IVA4B", "P_IVA4_BC"],
    "21": ["S_IVA21B", "P_IVA21_BC"],
    "0": ["S_IVA0", "P_IVA0_BC"]
}

TEMP_TYPE_MAP = {
    "D": "Seco",
    "N": "Refrigerado",
    "A": "Congelado"
}

def ustr(text):
    """convierte las cadenas de sql server en iso-8859-1 a utf-8 que es la cofificaciï¿œn de postgresql"""
    return unicode(text.strip(), 'iso-8859-15').encode('utf-8')

class DatabaseImport:
    """
    Importa a OpenERP datos de una base de datos SqlServer
    """

    def __init__(self, dbname, user, passwd, sql_server_host, sql_server_dbname):
        """
        Inicializar las opciones por defecto y conectar con OpenERP
        """


    #-------------------------------------------------------------------------
    #--- WRAPPER XMLRPC OPENERP ----------------------------------------------
    #-------------------------------------------------------------------------


        self.url_template = "http://%s:%s/xmlrpc/%s"
        self.server = "localhost"
        self.port = 9069
        self.dbname = dbname
        self.user_name = user
        self.user_passwd = passwd
        self.user_id = 0
        self.sql_server_host = sql_server_host
        self.sql_server_dbname = sql_server_dbname
        self.import_orders = []

        #
        # Conectamos con OpenERP
        #
        login_facade = xmlrpclib.ServerProxy(self.url_template % (self.server, self.port, 'common'))
        self.user_id = login_facade.login(self.dbname, self.user_name, self.user_passwd)
        self.object_facade = xmlrpclib.ServerProxy(self.url_template % (self.server, self.port, 'object'))

        #
        # Fichero Log de Excepciones
        #
        self.file = open("importation_log.txt", "w")

    def exception_handler(self, exception):
        """Manejador de Excepciones"""
        print "HANDLER: ", (exception)
        self.file.write("WARNING: %s\n\n\n" % repr(exception))
        return True

    def create(self, model, data, context={}):
        """
        Wrapper del método create.
        """
        try:
            res = self.object_facade.execute(self.dbname, self.user_id, self.user_passwd,
                                model, 'create', data, context)

            if isinstance(res, list):
                res = res[0]

            return res
        except socket.error, err:
            raise Exception(u'Conexión rechazada: %s!' % err)
        except xmlrpclib.Fault, err:
            raise Exception(u'Error %s en create: %s' % (err.faultCode, err.faultString))

    def exec_workflow(self, model, signal, ids):
        """ejecuta un workflow por xml rpc"""
        try:
            res = self.object_facade.exec_workflow(self.dbname, self.user_id, self.user_passwd, model, signal, ids)
            return res
        except socket.error, err:
            raise Exception(u'Conexión rechazada: %s!' % err)
        except xmlrpclib.Fault, err:
            raise Exception(u'Error %s en exec_workflow: %s' % (err.faultCode, err.faultString))

    def search(self, model, query, context={}):
        """
        Wrapper del método search.
        """
        try:
            ids = self.object_facade.execute(self.dbname, self.user_id, self.user_passwd,
                                model, 'search', query, context)
            return ids
        except socket.error, err:
            raise Exception(u'Conexión rechazada: %s!' % err)
        except xmlrpclib.Fault, err:
            raise Exception(u'Error %s en search: %s' % (err.faultCode, err.faultString))


    def read(self, model, ids, fields, context={}):
        """
        Wrapper del método read.
        """
        try:
            data = self.object_facade.execute(self.dbname, self.user_id, self.user_passwd,
                                    model, 'read', ids, fields, context)
            return data
        except socket.error, err:
            raise Exception(u'Conexión rechazada: %s!' % err)
        except xmlrpclib.Fault, err:
            raise Exception(u'Error %s en read: %s' % (err.faultCode, err.faultString))


    def write(self, model, ids, field_values, context={}):
        """
        Wrapper del método write.
        """
        try:
            res = self.object_facade.execute(self.dbname, self.user_id, self.user_passwd,
                                    model, 'write', ids, field_values, context)
            return res
        except socket.error, err:
            raise Exception(u'Conexión rechazada: %s!' % err)
        except xmlrpclib.Fault, err:
            raise Exception(u'Error %s en write: %s' % (err.faultCode, err.faultString))


    def unlink(self, model, ids, context={}):
        """
        Wrapper del método unlink.
        """
        try:
            res = self.object_facade.execute(self.dbname, self.user_id, self.user_passwd,
                                    model, 'unlink', ids, context)
            return res
        except socket.error, err:
            raise Exception(u'Conexión rechazada: %s!' % err)
        except xmlrpclib.Fault, err:
            raise Exception(u'Error %s en unlink: %s' % (err.faultCode, err.faultString))

    def default_get(self, model, fields_list=[], context={}):
        """
        Wrapper del método default_get.
        """
        try:
            res = self.object_facade.execute(self.dbname, self.user_id, self.user_passwd,
                                    model, 'default_get', fields_list, context)
            return res
        except socket.error, err:
            raise Exception('Conexión rechazada: %s!' % err)
        except xmlrpclib.Fault, err:
            raise Exception('Error %s en default_get: %s' % (err.faultCode, err.faultString))

    def execute(self, model, method, args = [], context={}):
        """
        Wrapper del método execute.
        """
        try:
            res = self.object_facade.execute(self.dbname, self.user_id, self.user_passwd,
                                    model, method, *args, **context)
            return res
        except socket.error, err:
            raise Exception('Conexión rechazada: %s!' % err)
        except xmlrpclib.Fault, err:
            raise Exception('Error %s en execute: %s' % (err.faultCode, err.faultString))

    def _getTaxes(self, tax_name):
        tax_ids = self.search("account.tax", [('description', '=', tax_name)])
        return tax_ids

    def _getTempType_byName(self, temp_name):
        temp_ids = self.search("temp.type", [("name", "=", temp_name)])
        return temp_ids and temp_ids[0] or False

    def import_products(self, cr, product_code):
        cr.execute("select v.articulo as default_code, v.descripcion as name, v.familia as categ_id_map, m.pr1_cenv as temp_type_map, "
                   "v.medida_base as uom_id_map, v.medida_composicion as uomb_map, v.cantidad_composicion as kg_un, m.pr1_tcom as var_coeff_un, "
                   "v.cajas_por_rellano as ca_ma, v.cajas_por_pale / nullif(v.cajas_por_rellano, 0) as ma_pa, v.control_stock as type_map, "
                   "v.codigo_iva as tax_map, v.ean_base as ean14, v.precio_ultima_compra as standard_price, v.bloqueado as active, "
                   "m.pr1_capl as weight, m.observaciones_articulo as description, v.tipo_composicion as base_use_sale, v.id as internal_code "
                   "from dbo.articulos v inner join dbo.adsd_art m on m.pr1_codi = v.articulo where v.articulo = ?", (product_code,))
        row = cr.fetchone()
        prod_id = False
        if row:
            uom_id = self.search("product.uom", [('name', '=', UOM_MAP[row.uom_id_map.strip()])])[0]
            uob_id = self.search("product.uom", [('name', '=', UOM_MAP[row.uomb_map.strip()])])[0]
            product_vals = {
                "default_code": str(int(row.default_code)),
                "name": ustr(row.name),
                "categ_id": 2,
                "uom_id": uom_id,
                "uom_po_id": uom_id,
                "log_unit_id": uom_id,
                "ca_ma": row.ca_ma or 0,
                "ma_pa": row.ma_pa or 0,
                "standard_price": row.standard_price,
                "weight": row.weight and row.weight / 1000.0 or 0.0,
                "description": (row.description and ustr(row.description) or "") + (row.active != "N" and "\nBLOQUEADO" or ""),
                "unit_use_sale": True,
                "type": TYPE_MAP[row.type_map],
                "purchase_ok": True,
                "sale_ok": True,
                "log_box_id": False,
                "log_base_id": False,
                "cost_method": "average",
                "taxes_id": [(6, 0, self._getTaxes(IVA_MAP[str(int(row.tax_map))][0]))],
                "supplier_taxes_id": [(6, 0, self._getTaxes(IVA_MAP[str(int(row.tax_map))][1]))],
                "ean14": row.ean14 and ustr(str(int(row.ean14))) or "",
                "temp_type": self._getTempType_byName(row.temp_type_map and TEMP_TYPE_MAP[row.temp_type_map] or TEMP_TYPE_MAP["D"]),
                "var_coeff_un": row.var_coeff_un == "V" and True or False,
                "internal_code": str(int(row.internal_code)),
                "track_all": True
            }
            if uom_id != uob_id:
                product_vals["log_base_id"] = uob_id
                product_vals["base_use_sale"] = row.base_use_sale == "S" and True or False


            res = self.search("product.product", [('default_code', '=', product_vals['default_code']),'|',('active', '=', False),('active', '=', True)])
            if not res:
                prod_id = self.create("product.product", product_vals)
            else:
                prod_id = res[0]

            cr.execute("select top 1 tari_prec as lst_price from dbo.adsd_tari where tari_arti = ? order by tari_desd desc", (row.default_code,))
            row2 = cr.fetchone()
            if row2 and row2.lst_price:
                self.write("product.product", [prod_id], {"lst_price": row2.lst_price})

        return prod_id

    def _create_or_update_partner(self, row, unregister_id,parent_id=False):
        partner_ids = self.search("res.partner", [('ref', '=', str(row[0])),('customer', '=', True),'|',('active', '=', True),('active', '=', False)])
        partner_vals = {'comercial': row[1] and ustr(row[1]) or "",
                        'name': ustr(row[2]),
                        'street': row[3] and ustr(row[3]) or "",
                        'zip': row[4] and ustr(row[4]) or "",
                        'city': row[5] and ustr(row[5]) or "",
                        'phone': row[6] and ustr(row[6]) or "",
                        'fax': row[8] and ustr(row[8]) or "",
                        "customer": True,
                        "comment": row[11] and ustr(row[11]) or "",
                        "email": row[10] and ustr(row[10]) or "",
                        "parent_id": parent_id,
                        "is_company": not parent_id and True or False
                        }
        if row[9]:
            partner_vals['state2'] = "unregistered"
            partner_vals['unregister_reason_id'] = unregister_id[0]
            partner_vals['comment'] += "\nFecha de baja: " + str(row[9])
            partner_vals['active'] = False
        insert_vat = False
        if not partner_ids:
            partner_vals['ref'] = str(row[0])
            partner_id = self.create("res.partner", partner_vals)

            if row[7] and len(ustr(row[7].replace(" ", "").replace("-",""))) == 9:
                insert_vat = True
        else:
            self.write("res.partner", [partner_ids[0]], partner_vals)
            partner_id = partner_ids[0]
            if row[7] and len(ustr(row[7].replace(" ", "").replace("-",""))) == 9:
                partner_data = self.read("res.partner", partner_id, ["vat"])
                if not partner_data["vat"]:
                    insert_vat = True
        if insert_vat:
            vat = u"ES" + ustr(row[7].replace(" ", "").replace("-",""))
            try:
                self.write("res.partner", [partner_id], {'vat': vat})
            except:
                print u"CIF no váĺido en España", row[7]

        return partner_id

    def import_customers(self, cr, customer_code):
        partner_id = False
        unregister_reason = u"Baja en importación"
        unregister_id = self.search("unregister.partner.reason", [("name", '=', unregister_reason)])

        cr.execute("select vc.cliente as ref, vc.nombre_comercial as comercial, vc.nombre_fiscal as name, vc.direccion as street,vc.codigo_postal as zip,"
                   "vc.poblacion as city, vc.telefono as phone, nullif(nullif(vc.nif, '0T'), '0') as vat_woc, c.cli_nfax as fax, c.fecha_baja as inactive_date,"
                   "c.email_comercial as email, c.observaciones as comment, c.cli_asoc as parent_id_map from dbo.LG_clientes vc "
                   "inner join dbo.adsd_clie c on c.cli_codi = vc.cliente where vc.cliente = ?", (customer_code,))
        row = cr.fetchone()
        if row:
            if row[12]:
                partner_parent_ids = self.search("res.partner", [('ref', '=', str(row[12])),('customer', '=', True),'|',('active', '=', True),('active', '=', False)])
            else:
                partner_parent_ids = False
            if partner_parent_ids:
                partner_id = self._create_or_update_partner(row, unregister_id, parent_id=partner_parent_ids[0])
            else:
                partner_id = self._create_or_update_partner(row, unregister_id)

        return partner_id

    def import_indirect_customer(self, cr, customer_code):
        cr.execute("select clpr_clie as customer_map, clpr_prov as supplier_map, clpr_copr as unilever_code from dbo.adsd_clpr where clpr_clie = ?", (customer_code,))
        customer_data = cr.fetchall()
        for row in customer_data:
            customer_ids = self.search("res.partner", [('ref', '=', str(row[0])),('customer', '=', True),'|',('active', '=', True),('active', '=', False)])
            supplier_ids = self.search("res.partner", [('ref', '=', str(row[1])),('supplier', '=', True),'|',('active', '=', True),('active', '=', False)])
            if customer_ids and supplier_ids:
                vals = {'supplier_ids': [(4,supplier_ids[0])],
                        'indirect_customer': True}
                if row[1] == 2: #unilever
                    vals['unilever_code'] = row[2] and str(int(row[2])) or ""
                self.write("res.partner", [customer_ids[0]], vals)

    def import_rel_product_supplier(self, cr, product_code):
        cr.execute("select v.articulo as default_code, v.proveedor as supplier_map, v.articulo_proveedor as supplier_code, v.medida_base as uom_id_map, v.medida_composicion as uomb_map,"
                   " v.tipo_composicion as base_use_purchase, v.cantidad_composicion as supp_kg_un, m.pr1_tcom as var_coeff_un, v.cajas_por_rellano as supp_ca_ma, "
                   " v.cajas_por_pale / nullif(v.cajas_por_rellano, 0) as supp_ma_pa from dbo.articulos v inner join dbo.adsd_art m on m.pr1_codi = v.articulo where v.proveedor != 100"
                   " and v.articulo = ?", (product_code,))
        product_data = cr.fetchall()
        for row in product_data:
            uom_id = self.search("product.uom", [('name', '=', UOM_MAP[row.uom_id_map.strip()])])[0]
            uob_id = self.search("product.uom", [('name', '=', UOM_MAP[row.uomb_map.strip()])])[0]
            supplier_ids = self.search("res.partner", [('ref', '=', str(row.supplier_map)),('supplier', '=', True),'|',('active', '=', True),('active', '=', False)])
            product_ids = self.search("product.product", [('default_code', '=',str(row.default_code)),'|',('active', '=', False),('active', '=', True)])
            if supplier_ids and product_ids:
                product_data = self.read("product.product", product_ids[0], ["product_tmpl_id"])
                supp_info_ids = self.search("product.supplierinfo", [('product_tmpl_id', '=', product_data['product_tmpl_id'][0]),('name', '=', supplier_ids[0])])
                if not supp_info_ids:
                    vals = {"product_tmpl_id": product_data['product_tmpl_id'][0],
                            "name": supplier_ids[0],
                            "product_code": str(row.supplier_code),
                            "log_unit_id": uom_id,
                            "unit_use_purchase": True,
                            "log_box_id": False,
                            "log_base_id": False,
                            "base_use_purchase": False,
                            "supp_ca_ma": row.supp_ca_ma or 0,
                            "supp_ma_pa": row.supp_ma_pa or 0,
                            "var_coeff_un": row.var_coeff_un == "V" and True or False}

                    if uom_id != uob_id:
                        vals["log_base_id"] = uob_id
                    self.create("product.supplierinfo", vals)

    def import_sale_orders(self, cr):
        ###################################################################
        ## Se importan cabeceras vivas e históricas desde el 17-8-2015
        #cr.execute("select numero_pedido as name, cliente as partner_id_map, fecha as date_order, Dia_reparto as date_planned, proveedor as supplier_id_map, "
        #           "observacion_pedido as customer_comment, observacion_reparto as note, pedido_sam as client_order_ref, 'draft' as state, '' as invoice_info, "
        #           "'' as picking_info from dbo.cabecera_pedido_ventas union "
        #           "select numero_pedido as name, cliente as partner_id_map, fecha_carga as date_order, Dia_reparto as date_planned, proveedor as supplier_id_map, "
        #           "'' as customer_comment, '' as note, '' as client_order_ref, 'history' as state, serie_factura + CONVERT(varchar, numero_factura) as invoice_info, "
        #           "numero_carga as picking_info from dbo.cabecera_pedido_copia where cast(fecha_carga as date) >= '2015-08-17 00:00:00'")
        ###################################################################
        ## Se importan sólo pedidos vivos
        cr.execute("select numero_pedido as name, cliente as partner_id_map, fecha as date_order, Dia_reparto as date_planned, proveedor as supplier_id_map, "
                    "observacion_pedido as customer_comment, observacion_reparto as note, pedido_sam as client_order_ref, 'draft' as state, '' as invoice_info, "
                    "'' as picking_info from dbo.cabecera_pedido_ventas")
        ###################################################################
        ## Se importan sólo pedidos históricos
        #cr.execute("select numero_pedido as name, cliente as partner_id_map, fecha_carga as date_order, Dia_reparto as date_planned, proveedor as supplier_id_map, "
        #           "'' as customer_comment, '' as note, '' as client_order_ref, 'history' as state, serie_factura + CONVERT(varchar, numero_factura) as invoice_info, "
        #           "numero_carga as picking_info from dbo.cabecera_pedido_copia")
        ###################################################################
        #cr.execute("select numero_pedido as name, cliente as partner_id_map, fecha as date_order, Dia_reparto as date_planned, proveedor as supplier_id_map, "
        #          "observacion_pedido as customer_comment, observacion_reparto as note, pedido_sam as client_order_ref, 'draft' as state, '' as invoice_info, "
        #           "'' as picking_info from dbo.cabecera_pedido_ventas union "
        #           "select numero_pedido as name, cliente as partner_id_map, fecha_carga as date_order, Dia_reparto as date_planned, proveedor as supplier_id_map, "
        #           "'' as customer_comment, '' as note, '' as client_order_ref, 'history' as state, serie_factura + CONVERT(varchar, numero_factura) as invoice_info, "
        #           "numero_carga as picking_info from dbo.cabecera_pedido_copia")
        data = cr.fetchall()
        num_rows = len(data)
        cont = 0
        for row in data:
            order_ids = self.search("sale.order", [('name','=',str(int(row.name)))])
            if order_ids:
                cont += 1
                print "%s de %s" % (str(cont), str(num_rows))
                continue
            partner_ids = self.search("res.partner", [('ref', '=', str(int(row.partner_id_map))),('customer','=',True),'|',('active','=',True),('active','=',False)])
            if not partner_ids:
                partner_id = self.import_customers(cr, int(row.partner_id_map))
                if not partner_id:
                    print "No hay un cliente con codigo ", str(int(row.partner_id_map))
                    cont += 1
                    print "%s de %s" % (str(cont), str(num_rows))
                    continue
            else:
                partner_id = partner_ids[0]
            if row.supplier_id_map:
                supplier_ids = self.search("res.partner", [('ref', '=', str(int(row.supplier_id_map))),('supplier','=',True),'|',('active','=',True),('active','=',False)])
                if not supplier_ids:
                    raise Exception("No hay un proveedor con el codigo %s" % int(row.supplier_id_map))
                self.import_indirect_customer(cr, int(row.partner_id_map))

            sale_vals = {
                'name': str(int(row.name)),
                'partner_id': partner_id,
                'partner_invoice_id': partner_id,
                'partner_shipping_id': partner_id,
                'date_order': row.date_order and row.date_order.strftime("%Y-%m-%d %H:%M:%S") or time.strftime("%Y-%m-%d %H:%M:%S"),
                'date_planned': row.date_planned and row.date_planned.strftime("%Y-%m-%d %H:%M:%S") or False,
                'supplier_id': row.supplier_id_map and supplier_ids[0] or False,
                'customer_comment': ((row.customer_comment and row.customer_comment.strip() != "") and ustr(row.customer_comment) or ""),
                'note': ((row.note and row.note.strip() != "") and ustr(row.note) or "") + ((row.invoice_info and row.invoice_info.strip() != "") and "\nFACTURA: " + row.invoice_info or "") + ((row.picking_info and row.picking_info != " " and row.picking_info != -1 and str(int(row.picking_info)).strip() != "") and "\nALBARAN: " + str(int(row.picking_info)) or ""),
                'client_order_ref': row.client_order_ref or False,
                'state': row.state
            }
            order_id = self.create("sale.order", sale_vals)
            #if row.state == 'history':
            #    self.import_orders.append(int(row.name))

            cont += 1
            print "%s de %s" % (str(cont), str(num_rows))

    def import_sale_order_lines_open(self, cr):
        #Lineas abiertas
        cr.execute("select numero_pedido as order_id_map, numero_linea as sequence, producto as product_id_map, descripcion as name, cajas as box_qty, composicion as unit_qty, "
                   "precio as price_unit, dcto as discount, tipo_iva as tax_id_map, 'draft' as state from dbo.lineas_pedido_ventas")
        data = cr.fetchall()
        num_rows = len(data)
        cont = 0
        print "no. lineas abiertas: ", num_rows
        for row in data:
            sale_ids = self.search("sale.order", [('name', '=', str(int(row.order_id_map)))])
            if not sale_ids:
                print "No se ha encontrado un pedido con la referencia ", int(row.order_id_map)
                cont += 1
                print "%s de %s" % (str(cont), str(num_rows))
                continue

            product_ids = self.search("product.product", [('default_code', '=', str(int(row.product_id_map))),'|',('active','=',True),('active','=',False)])
            if not product_ids:
                product_id = self.import_products(cr, int(row.product_id_map))
                self.import_rel_product_supplier(cr, int(row.product_id_map))
            else:
                product_id = product_ids[0]

            product_data = self.read("product.product", product_id, ["uom_id", "log_unit_id", "log_base_id", "log_box_id"])
            loc_qty = row.box_qty
            if row.unit_qty:
                if product_data["log_base_id"]:
                    unit = product_data["log_base_id"][0]
                elif product_data["log_unit_id"]:
                    unit = product_data["log_unit_id"][0]
                else:
                    unit = product_data["log_box_id"][0]
                if unit:
                    print "initial loc_qty: ", loc_qty
                    loc_qty += self.execute("product.product", "uos_qty_to_uom_qty", [product_id, row.unit_qty, unit])
                    print "end loc_qty: ", loc_qty

            line_vals = {'order_id': sale_ids[0],
                         'sequence': row.sequence,
                         'product_id': product_id,
                         'product_uom': product_data["uom_id"][0],
                         'product_uos': product_data["uom_id"][0],
                         'product_uom_qty': loc_qty,
                         'product_uos_qty': loc_qty,
                         'price_unit': row.price_unit,
                         'price_udv': row.price_unit,
                         'name': ustr(row.name),
                         'discount': row.discount,
                         'tax_id': [(6, 0, self._getTaxes(IVA_MAP[str(int(row.tax_id_map))][0]))],
                         'state': row.state}
            self.create("sale.order.line", line_vals)
            cont += 1
            print "%s de %s" % (str(cont), str(num_rows))

    def import_sale_order_lines_history(self, cr):
        #Lineas históricas
        ###################################################################
        ## Se importan lineas históricas desde el 17-8-2015
        #cr.execute("select dbo.lineas_pedido_copia.numero_pedido as order_id_map, numero_linea as sequence, producto as product_id_map, descripcion as name, cajas as box_qty, composicion as unit_qty, "
        #           "importe as price_subtotal, tipo_iva as tax_id_map, 'history' as state from dbo.lineas_pedido_copia"
        #           " inner join dbo.cabecera_pedido_copia on dbo.cabecera_pedido_copia.numero_pedido = dbo.lineas_pedido_copia.numero_pedido where cast(fecha_carga as date) >= '2015-08-17 00:00:00'")
        ###################################################################
        ## Se importan todas las lineas históricas
        #cr.execute("select dbo.lineas_pedido_copia.numero_pedido as order_id_map, numero_linea as sequence, producto as product_id_map, descripcion as name, cajas as box_qty, composicion as unit_qty, "
        #           "importe as price_subtotal, tipo_iva as tax_id_map, 'history' as state from dbo.lineas_pedido_copia")
        ###################################################################
        ## Lineas históricas de ciertos pedidos
        cr.execute("select dbo.lineas_pedido_copia.numero_pedido as order_id_map, numero_linea as sequence, producto as product_id_map, descripcion as name, cajas as box_qty, composicion as unit_qty, "
                   "importe as price_subtotal, tipo_iva as tax_id_map, 'history' as state from dbo.lineas_pedido_copia where numero_pedido in ?",(tuple(self.import_orders),))
        data = cr.fetchall()
        num_rows = len(data)
        cont = 0
        print "no. lineas historicas: ", num_rows
        for row in data:
            sale_ids = self.search("sale.order", [('name', '=', str(int(row.order_id_map)))])
            if not sale_ids:
                print "No se ha encontrado un pedido con la referencia ", int(row.order_id_map)
                cont += 1
                print "%s de %s" % (str(cont), str(num_rows))
                continue

            product_ids = self.search("product.product", [('default_code', '=', str(int(row.product_id_map))),'|',('active','=',True),('active','=',False)])
            if not product_ids:
                product_id = self.import_products(cr, int(row.product_id_map))
                self.import_rel_product_supplier(cr, int(row.product_id_map))
            else:
                product_id = product_ids[0]
            if product_id:
                product_data = self.read("product.product", product_id, ["uom_id", "log_unit_id", "log_base_id", "log_box_id"])
                uom_id = product_data["uom_id"][0]
                loc_qty = row.box_qty
                if row.unit_qty:
                    if product_data["log_base_id"]:
                        unit = product_data["log_base_id"][0]
                    elif product_data["log_unit_id"]:
                        unit = product_data["log_unit_id"][0]
                    else:
                        unit = product_data["log_box_id"][0]
                    if unit:
                        print "initial loc_qty: ", loc_qty
                        loc_qty += self.execute("product.product", "uos_qty_to_uom_qty", [product_id, row.unit_qty, unit])
                        print "end loc_qty: ", loc_qty
            else:
                 loc_qty = row.box_qty + row.unit_qty
                 uom_id = 1

            line_vals = {'order_id': sale_ids[0],
                         'sequence': row.sequence,
                         'product_id': product_id,
                         'product_uom': uom_id,
                         'product_uos': uom_id,
                         'product_uom_qty': loc_qty or 1.0,
                         'product_uos_qty': loc_qty or 1.0,
                         'price_unit': row.price_subtotal / (loc_qty or 1.0),
                         'price_udv': row.price_subtotal / (loc_qty or 1.0),
                         'name': ustr(row.name),
                         'tax_id': [(6, 0, self._getTaxes(IVA_MAP[str(int(row.tax_id_map))][0]))],
                         'state': row.state}
            self.create("sale.order.line", line_vals)
            cont += 1
            print "%s de %s" % (str(cont), str(num_rows))

    def import_active_purchase_order(self, cr):
        cr.execute("select proveedor as supplier_id_map, fecha_pedido as date_order, fecha_recepcion as minimum_planned_date, pedido as name from "
                   "cabecera_pedidos_compra where situacion = 'V'")
        purchase_data = cr.fetchall()
        num_rows = len(purchase_data)
        cont = 0
        warehouse_ids = self.search("stock.warehouse", [])
        warehouse_data = self.read("stock.warehouse", warehouse_ids[0], ["wh_input_stock_loc_id"])
        for order in purchase_data:
            if str(int(order.supplier_id_map)) == "101":
                supp_id = "2"
            else:
                supp_id = str(int(order.supplier_id_map))
            print "Supp: ", supp_id
            supplier_ids = self.search("res.partner", [('ref', '=', supp_id),('supplier', '=', True),'|',('active', '=', True),('active', '=', False)])
            if supplier_ids:
                supplier_vals = self.read("res.partner", supplier_ids[0], ["property_product_pricelist_purchase"])
                purchase_vals = {
                    'partner_id': supplier_ids[0],
                    'name': str(int(order.name)),
                    'date_order': order.date_order.strftime("%Y-%m-%d"),
                    'minimum_planned_date': order.minimum_planned_date.strftime("%Y-%m-%d"),
                    'location_id': warehouse_data["wh_input_stock_loc_id"][0],
                    'pricelist_id': supplier_vals["property_product_pricelist_purchase"][0]
                }
                purchase_id = self.create("purchase.order", purchase_vals)

                cr.execute("select num_ped as order_id_map, ref_art as product_id_map, vta_bas as product_qty, tar_pro as price_unit, por_dto as discount, "
                           "por_iva as tax_id_map from dbo.adsd_pedi where num_ped = ?", (int(order.name),))
                lines_data = cr.fetchall()
                for row in lines_data:
                    print "Product: ", str(int(row.product_id_map))
                    product_ids = self.search("product.product", [('default_code', '=', str(int(row.product_id_map))),'|',('active', '=', True),('active', '=', False)])
                    if not product_ids:
                        product_id = self.import_products(cr, int(row.product_id_map))
                        self.import_rel_product_supplier(cr, int(row.product_id_map))
                    else:
                        product_id = product_ids[0]

                    product_data = self.read("product.product", product_id, ["product_tmpl_id", "name", "uom_id"])
                    supp_info_ids = self.search("product.supplierinfo", [('product_tmpl_id', '=', product_data['product_tmpl_id'][0]),('name', '=', supplier_ids[0])])
                    name = ""
                    if supp_info_ids:
                        supp_data = self.read("product.supplierinfo", supp_info_ids[0], ["product_code", "product_name"])
                        if supp_data["product_code"]:
                            name += u"[" + supp_data["product_code"] + u"] "
                        if supp_data["product_name"]:
                            name += supp_data["product_name"]
                        else:
                            name += product_data["name"]

                    if not name:
                        name += product_data["name"]
                    line_vals = {
                        'order_id': purchase_id,
                        'product_id': product_id,
                        'name': name,
                        'date_planned': order.minimum_planned_date.strftime("%Y-%m-%d"),
                        'product_uoc_qty': float(row.product_qty),
                        'product_uoc': product_data["uom_id"][0],
                        'price_udc': float(row.price_unit),
                        'product_qty': float(row.product_qty),
                        'product_uom': product_data["uom_id"][0],
                        'price_unit': float(row.price_unit),
                        'discount': float(row.discount),
                        'taxes_id': [(6, 0, self._getTaxes(IVA_MAP[str(int(row.tax_id_map))][1]))],
                    }
                    self.create("purchase.order.line", line_vals)
            cont += 1
            print "%s de %s" % (str(cont), str(num_rows))

    def import_purchase_invoice(self, cr):
        account_id = self.search("account.account", [('code', '=', "600000000")])[0]
        journal_id = self.search("account.journal", [('name', '=', "Diario de compras")])[0]
        cr.execute("select dic_prov as supplier_id_map, dic_nume as inv_number, dic_femi as invoice_date, "
                   "descuento_pp as ep_discount, fecha_vencimiento as due_date from dbo.adsd_dic")
        purchase_invoice_data = cr.fetchall()
        num_rows = len(purchase_invoice_data)
        cont = 0
        for row in purchase_invoice_data:
            supplier_ids = self.search("res.partner", [('supplier', '=', True),('ref', '=', str(int(row.supplier_id_map))),'|',('active', '=', True),('active', '=', False)])
            if supplier_ids:
                sup_data = self.read("res.partner", supplier_ids[0], ["property_account_payable"])
                invoice_vals = {
                    "number": str(int(row.inv_number)) + " " + str(cont+1),
                    "invoice_number": str(int(row.inv_number)) + " " + str(cont+1),
                    "reference": str(int(row.inv_number)),
                    "supplier_invoice_number": str(int(row.inv_number)),
                    "account_id": sup_data["property_account_payable"][0],
                    "partner_id": supplier_ids[0],
                    "date_invoice": row.invoice_date.strftime("%Y-%m-%d"),
                    "date_due": row.due_date.strftime("%Y-%m-%d"),
                    "state": "history",
                    "journal_id": journal_id,
                    "type": "in_invoice"
                }
                invoice_id = self.create("account.invoice", invoice_vals)
                cr.execute("select producto as product_id_map, base as uom_qty, composicion as base_qty, "
                           "tarifa as gross_price_unit, descuento as discount, iva as tax_id_map from "
                           "dbo.lineas_factura_compra where factura = ? and proveedor = ?", (int(row.inv_number),int(row.supplier_id_map),))
                lines_data = cr.fetchall()
                for line in lines_data:
                    product_ids = self.search("product.product", [('default_code', '=', str(int(line.product_id_map))),'|',('active','=',True),('active','=',False)])
                    if product_ids:
                        product_data = self.read("product.product", product_ids[0], ["name"])
                        product_id = product_ids[0]
                        line_name = product_data["name"]
                    else:
                        product_id = self.import_products(cr, int(line.product_id_map))
                        product_data = self.read("product.product", product_id, ["name"])
                        line_name = product_data["name"]

                    product_data = self.read("product.product", product_id, ["uom_id", "log_unit_id", "log_base_id", "log_box_id"])
                    uom_id = product_data["uom_id"][0]
                    loc_qty = line.uom_qty
                    if line.base_qty:
                        if product_data["log_base_id"]:
                            unit = product_data["log_base_id"][0]
                        elif product_data["log_unit_id"]:
                            unit = product_data["log_unit_id"][0]
                        else:
                            unit = product_data["log_box_id"][0]
                        if unit:
                            print "initial loc_qty: ", loc_qty
                            loc_qty += self.execute("product.product", "uos_qty_to_uom_qty", [product_id, line.base_qty, unit])
                            print "end loc_qty: ", loc_qty

                    if line.discount:
                        discount = float(line.discount) / 100.0
                        price_unit = float(line.gross_price_unit) * (1 - discount / 100.0)
                    else:
                        price_unit = float(line.gross_price_unit)
                    line_vals = {
                        "product_id": product_id,
                        "name": line_name,
                        "account_id": account_id,
                        "quantity": loc_qty,
                        "uos_id": uom_id,
                        "price_unit": price_unit,
                        "discount": row.ep_discount and float(row.ep_discount) or 0.0,
                        "invoice_line_tax_id": [(6, 0, self._getTaxes(IVAA_MAP[str(int(line.tax_id_map))][1]))],
                        "invoice_id": invoice_id
                    }
                    self.create("account.invoice.line", line_vals)
            self.execute("account.invoice", "button_reset_taxes", [[invoice_id]])
            cont += 1
            print "%s de %s" % (str(cont), str(num_rows))

    def import_sale_invoice(self, cr):
        account_id = self.search("account.account", [('code', '=', "700000000")])[0]
        journal_id = self.search("account.journal", [('name', '=', "Diario de ventas")])[0]
        cr.execute("select serie as number_pref, documento as number, fecha_contabilizacion as invoice_date, "
                   "cli_codi as partner_id_map, vencimiento as due_date from dbo.diario_ventas inner join "
                   "dbo.adsd_clie on dbo.adsd_clie.id_cliente = dbo.diario_ventas.cliente_id")
        invoice_data = cr.fetchall()
        num_rows = len(invoice_data)
        cont = 0
        for row in invoice_data:
            invoice_ids = self.search("account.invoice", [('type','=','out_invoice'),("number",'=',ustr(row.number_pref) + "/" + str(int(row.number)))])
            if invoice_ids:
                cont += 1
                continue
            customer_ids = self.search("res.partner", [('customer', '=', True),('ref', '=', str(int(row.partner_id_map))),'|',('active', '=', True),('active', '=', False)])
            if customer_ids:
                cust_data = self.read("res.partner", customer_ids[0], ["property_account_receivable"])

                invoice_vals = {
                    "number": ustr(row.number_pref) + "/" + str(int(row.number)),
                    "invoice_number": ustr(row.number_pref) + "/" + str(int(row.number)),
                    "account_id": cust_data["property_account_receivable"][0],
                    "partner_id": customer_ids[0],
                    "date_invoice": row.invoice_date.strftime("%Y-%m-%d"),
                    "date_due": row.due_date and row.due_date.strftime("%Y-%m-%d") or False,
                    "state": "history",
                    "journal_id": journal_id,
                    "type": "out_invoice"
                }
                invoice_id = self.create("account.invoice", invoice_vals)
                cr.execute("select producto as product_id_map, base as uom_qty, composicion as base_qty, "
                           "precio as price_unit, descuento as discount, iva as tax_id_map, descripcion as name from "
                           "dbo.lineas_mensual where serie = ? and numero = ?", (row.number_pref,int(row.number),))
                lines_data = cr.fetchall()
                for line in lines_data:
                    if line.product_id_map:
                        product_ids = self.search("product.product", [('default_code', '=', str(int(line.product_id_map))),'|',('active','=',True),('active','=',False)])
                        if product_ids:
                            product_id = product_ids[0]
                        else:
                            product_id = self.import_products(cr, int(line.product_id_map))
                    else:
                        product_id = False

                    if product_id:
                        product_data = self.read("product.product", product_id, ["uom_id", "log_unit_id", "log_base_id", "log_box_id"])
                        uom_id = product_data["uom_id"][0]
                        loc_qty = line.uom_qty
                        if line.base_qty:
                            if product_data["log_base_id"]:
                                unit = product_data["log_base_id"][0]
                            elif product_data["log_unit_id"]:
                                unit = product_data["log_unit_id"][0]
                            else:
                                unit = product_data["log_box_id"][0]
                            if unit:
                                print "initial loc_qty: ", loc_qty
                                loc_qty += self.execute("product.product", "uos_qty_to_uom_qty", [product_id, line.base_qty, unit])
                                print "end loc_qty: ", loc_qty
                    else:
                        loc_qty = line.uom_qty
                        uom_id = 1

                    line_vals = {
                        "product_id": product_id,
                        "name": ustr(line.name),
                        "account_id": account_id,
                        "quantity": loc_qty,
                        "uos_id": uom_id,
                        "price_unit": float(line.price_unit),
                        "discount": line.discount and float(line.discount) or 0.0,
                        "invoice_line_tax_id": [(6, 0, self._getTaxes(IVAA_MAP[str(int(line.tax_id_map))][0]))],
                        "invoice_id": invoice_id
                    }
                    self.create("account.invoice.line", line_vals)
                self.execute("account.invoice", "button_reset_taxes", [[invoice_id]])
                cont += 1
                print "%s de %s" % (str(cont), str(num_rows))

    def process_data(self):
        """
        Importa la bbdd
        """
        print "Intentamos establecer conexion"
        try:
            #
            # Nos conectamos a la bbdd de sql server
            #
            conn = pyodbc.connect("DRIVER={FreeTDS};SERVER=" + self.sql_server_host + ";UID=midban;PWD=midban2015;DATABASE=" + self.sql_server_dbname + ";Port=1433;TDS_Version=10.0")
            cr = conn.cursor()

            #self.import_sale_orders(cr)
            #self.import_sale_order_lines_open(cr)
            #self.import_sale_order_lines_history(cr)
            #self.import_active_purchase_order(cr)
            #self.import_purchase_invoice(cr)
            self.import_sale_invoice(cr)

        except Exception, ex:
            print u"Error al conectarse a las bbdd: ", repr(ex)
            sys.exit()

        self.file.write(u"Iniciamos la Importacion\n\n")


        #cerramos el fichero
        self.file.close()

        return True

if __name__ == "__main__":
    if len(sys.argv) < 6:
        print u"Uso: %s <dbname> <user> <password> <sql_server_host> <sql_server_dbname>" % sys.argv[0]
    else:
        ENGINE = DatabaseImport(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5])

        ENGINE.process_data()
