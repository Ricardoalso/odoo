# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

<<<<<<< HEAD
from odoo.addons.account.tests.account_test_savepoint import AccountTestInvoicingCommon
from odoo.tests import common, Form

QR_IBAN = 'CH21 3080 8001 2345 6782 7'
ISR_SUBS_NUMBER = "01-162-8"


class TestGenISRReference(AccountTestInvoicingCommon):
    """Check condition of generation of and content of the structured ref"""

    @classmethod
    def setUpClass(cls, chart_template_ref="l10n_ch.l10nch_chart_template"):
        super().setUpClass(chart_template_ref=chart_template_ref)
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
=======
from odoo.tests import common, Form


class TestGenISRReference(common.SavepointCase):
    """Check condition of generation of and content of the structured ref"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.partner = cls.env.ref("base.res_partner_12")
>>>>>>> 952301c7835436e82b70ee89cc50146f68e423ad
        cls.bank = cls.env["res.bank"].create(
            {
                "name": "Alternative Bank Schweiz AG",
                "bic": "ALSWCH21XXX",
            }
        )
<<<<<<< HEAD
        cls.bank_acc_isr = cls.env["res.partner.bank"].create(
=======
        cls.bank_acc = cls.env["res.partner.bank"].create(
>>>>>>> 952301c7835436e82b70ee89cc50146f68e423ad
            {
                "acc_number": "ISR",
                "l10n_ch_isr_subscription_chf": "01-162-8",
                "bank_id": cls.bank.id,
<<<<<<< HEAD
                "partner_id": cls.partner_a.id,
            }
        )
        cls.bank_acc_qriban = cls.env["res.partner.bank"].create(
            {
                "acc_number": QR_IBAN,
                "bank_id": cls.bank.id,
                "partner_id": cls.partner_a.id,
            }
        )
        cls.invoice = cls.init_invoice("out_invoice")

    def test_isr(self):

        self.invoice.invoice_partner_bank_id = self.bank_acc_isr
        self.invoice.name = "INV/01234567890"

        expected_isr = "000000000000000012345678903"
        expected_optical_line = "0100001307807>000000000000000012345678903+ 010001628>"
        self.assertEqual(self.invoice.l10n_ch_isr_number, expected_isr)
        self.assertEqual(self.invoice.l10n_ch_isr_optical_line, expected_optical_line)

    def test_qrr(self):
        self.invoice.invoice_partner_bank_id = self.bank_acc_qriban

        self.invoice.name = "INV/01234567890"

        expected_isr = "000000000000000012345678903"
        self.assertEqual(self.invoice.l10n_ch_isr_number, expected_isr)
        # No need to check optical line, we have no use for it with QR-bill

    def test_isr_long_reference(self):
        self.invoice.invoice_partner_bank_id = self.bank_acc_isr

        self.invoice.name = "INV/123456789012345678901234567890"

        expected_isr = "567890123456789012345678901"
        expected_optical_line = "0100001307807>567890123456789012345678901+ 010001628>"
        self.assertEqual(self.invoice.l10n_ch_isr_number, expected_isr)
        self.assertEqual(self.invoice.l10n_ch_isr_optical_line, expected_optical_line)

    def test_missing_isr_subscription_num(self):
        self.bank_acc_isr.l10n_ch_isr_subscription_chf = False

        self.invoice.invoice_partner_bank_id = self.bank_acc_isr

        self.assertFalse(self.invoice.l10n_ch_isr_number)
        self.assertFalse(self.invoice.l10n_ch_isr_optical_line)

    def test_missing_isr_subscription_num_in_wrong_field(self):
        self.bank_acc_isr.l10n_ch_isr_subscription_chf = False
        self.bank_acc_isr.l10n_ch_postal = ISR_SUBS_NUMBER

        self.invoice.invoice_partner_bank_id = self.bank_acc_isr

        self.assertFalse(self.invoice.l10n_ch_isr_number)
        self.assertFalse(self.invoice.l10n_ch_isr_optical_line)

    def test_no_bank_account(self):
        self.invoice.invoice_partner_bank_id = False

        self.assertFalse(self.invoice.l10n_ch_isr_number)
        self.assertFalse(self.invoice.l10n_ch_isr_optical_line)

    def test_wrong_currency(self):
        self.invoice.invoice_partner_bank_id = self.bank_acc_isr
        self.invoice.currency_id = self.env.ref("base.BTN")

        self.assertFalse(self.invoice.l10n_ch_isr_number)
        self.assertFalse(self.invoice.l10n_ch_isr_optical_line)
=======
                "partner_id": cls.partner.id,
            }
        )

    def new_form(self):
        inv = Form(self.env["account.move"].with_context(
            default_type="out_invoice")
        )
        inv.partner_id = self.partner
        inv.currency_id = self.env.ref("base.CHF")
        with inv.invoice_line_ids.new() as line:
            line.name = "Fondue Party"
            line.price_unit = 494.
        return inv

    def test_isr(self):
        inv_form = self.new_form()
        inv_form.invoice_partner_bank_id = self.bank_acc
        invoice = inv_form.save()

        invoice.name = "INV/01234567890"

        expected_isr = "000000000000000012345678903"
        expected_optical_line = (
            "0100000494004>000000000000000012345678903+ 010001628>"
        )
        self.assertEqual(invoice.l10n_ch_isr_number, expected_isr)
        self.assertEqual(invoice.l10n_ch_isr_optical_line, expected_optical_line)

    def test_isr_long_reference(self):
        inv_form = self.new_form()
        inv_form.invoice_partner_bank_id = self.bank_acc
        invoice = inv_form.save()

        invoice.name = "INV/123456789012345678901234567890"

        expected_isr = "567890123456789012345678901"
        expected_optical_line = (
            "0100000494004>567890123456789012345678901+ 010001628>"
        )
        self.assertEqual(invoice.l10n_ch_isr_number, expected_isr)
        self.assertEqual(invoice.l10n_ch_isr_optical_line, expected_optical_line)

    def test_missing_isr_subscription_num(self):
        self.bank_acc.l10n_ch_isr_subscription_chf = False

        inv_form = self.new_form()
        inv_form.invoice_partner_bank_id = self.bank_acc
        invoice = inv_form.save()
        self.assertFalse(invoice.l10n_ch_isr_number)
        self.assertFalse(invoice.l10n_ch_isr_optical_line)

    def test_no_bank_account(self):
        inv_form = self.new_form()
        inv_form.invoice_partner_bank_id = self.env["res.partner.bank"]
        invoice = inv_form.save()

        self.assertFalse(invoice.l10n_ch_isr_number)
        self.assertFalse(invoice.l10n_ch_isr_optical_line)

    def test_wrong_currency(self):
        inv_form = self.new_form()
        inv_form.invoice_partner_bank_id = self.bank_acc
        inv_form.currency_id = self.env.ref("base.BTN")
        invoice = inv_form.save()

        self.assertFalse(invoice.l10n_ch_isr_number)
        self.assertFalse(invoice.l10n_ch_isr_optical_line)
>>>>>>> 952301c7835436e82b70ee89cc50146f68e423ad
