1. En la base de datos local borramos todo apuntes contable, asiento, conciliación y apunte analítico que haya.
        delete from account_move_reconcile;
        delete from account_move;
        delete from account_voucher;
        delete from account_bank_statement_line;
        delete from account_bank_statement;
        delete from account_asset_asset;
2. Ver los registros creados por el script lanzado en amazon para crearlos también o mapear sus ids en local.
        select * from res_partner where create_date > '2015-11-28 08:00:00' (0 resultados)
        select * from account_account where create_date > '2015-11-28 08:00:00'; (0 resultados)
        select * from account_period where create_date > '2015-11-26 08:00:00';
3. Borras las tablas de asientos, apuntes, conciliacion y apuntes analíticos y sus dependencias de la base de datos local
        drop view account_treasury_report;
        drop view account_followup_stat_by_partner;
        drop view report_account_receivable;
        drop view account_entries_report;
        drop view account_followup_stat;
        drop view analytic_entries_report;
        drop table account_analytic_line;
        drop view sale_receipt_report;
        drop table account_move_line_l10n_es_aeat_tax_line_rel;
        drop table account_move_line_relation;
        drop table account_voucher_line;
        drop table l10n_es_aeat_mod347_cash_record;
        drop table line_pay_rel;
        drop table mod111_account_move_line08_rel;
        drop table mod111_account_move_line09_rel;
        drop table mod115_account_move_line02_rel;
        drop table mod115_account_move_line03_rel;
        drop table payment_line_rel_;
        drop table payment_line;
        drop table set_partner_in_move_move_line_rel;
        drop table account_move_line;
        drop view asset_asset_report;
        drop table account_asset_depreciation_line;
        drop table account_bank_statement_line;
        drop table account_fiscalyear_closing_c_account_map;
        drop table account_fiscalyear_closing_lp_account_map;
        drop table account_fiscalyear_closing_nlp_account_map;
        drop table account_fiscalyear_closing;
        alter table account_invoice drop column move_id;
        drop table account_subscription_line;
        drop table account_voucher;
        drop table account_period_l10n_es_aeat_mod111_report_rel;
        drop table l10n_es_aeat_mod111_report;
        drop table account_period_l10n_es_aeat_mod115_report_rel;
        drop table l10n_es_aeat_mod115_report;
        drop table account_period_l10n_es_aeat_mod130_report_rel;
        drop table l10n_es_aeat_mod130_report;
        drop table account_period_l10n_es_aeat_mod303_report_rel;
        drop table l10n_es_aeat_mod303_report;
        drop table l10n_es_aeat_mod340_investment;
        drop table l10n_es_aeat_mod340_tax_line_issued;
        drop table l10n_es_aeat_mod340_issued;
        drop table l10n_es_aeat_mod340_tax_line_received;
        drop table l10n_es_aeat_mod340_received;
        drop table l10n_es_aeat_mod340_intracomunitarias;
        drop table account_period_l10n_es_aeat_mod340_report_rel;
        drop table l10n_es_aeat_mod340_report;
        drop table account_period_l10n_es_aeat_mod347_report_rel;
        drop table l10n_es_aeat_mod347_invoice_record;
        drop table l10n_es_aeat_mod347_partner_record;
        drop table l10n_es_aeat_mod347_real_estate_record;
        drop table l10n_es_aeat_mod347_real_state_record;
        drop table l10n_es_aeat_mod347_report;
        drop table l10n_es_aeat_mod349_partner_record_detail;
        drop table l10n_es_aeat_mod349_partner_record;
        drop table account_period_l10n_es_aeat_mod349_report_rel;
        drop table l10n_es_aeat_mod349_partner_refund_detail;
        drop table l10n_es_aeat_mod349_partner_refund;
        drop table mod349_mod349_period_rel;
        drop table set_invoice_ref_in_move_move_rel;
        alter table stock_picking drop column pending_invoice_move_id;
        drop table account_move;
        drop table account_move_reconcile;
        drop table account_move_line_reconcile;
4. Volcamos las tablas
        pg_dump -U oerp -t account_move_reconcile apolo_amazon | psql -U oerp -d apolo_local
        pg_dump -U oerp -t account_move apolo_amazon | psql -U oerp -d apolo_local
        pg_dump -U oerp -t account_move_line apolo_amazon | psql -U oerp -d apolo_local
        pg_dump -U oerp -t account_analytic_line apolo_amazon | psql -U oerp -d apolo_local
