# -*- coding: utf-8 -*-
from odoo import models


class PaymentRegister(models.TransientModel):
    """Backport from v13 of extend of account.payment.register"""
    _inherit = "account.register.payments"

    def _prepare_communication(self, invoices):
        """Return a single ISR reference

        to avoid duplicate of the same number when multiple payments are done
        on the same reference. As those payments are grouped by reference,
        we want a unique reference in communication.

        """
        # Only the first invoice needs to be tested as the grouping ensure
        # invoice with same ISR are in the same group.
        if invoices[0]._is_isr_supplier_invoice():
            return invoices[0].reference
        else:
            return super()._prepare_communication(invoices)

    def _get_payment_group_key(self, inv):
        """Define group key to group invoices in payments.
        In case of ISR reference number on the supplier invoice
        the group rule must separate the invoices by payment refs.

        As such reference is structured. This is required to export payments
        to bank in batch.
        """
        if inv._is_isr_supplier_invoice():
            ref = inv.reference
            return (inv.commercial_partner_id, inv.currency_id, inv.partner_bank_id, ref)
        else:
            return super()._get_payment_group_key(inv)
