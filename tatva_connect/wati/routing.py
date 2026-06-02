"""Route a WhatsApp Message to the correct WATI account by the lead's taxonomy.

One WATI tenant = one `WhatsApp Account`. A `WATI Account Routing` rule maps a
Product Line (CRM Vertical) / Group (CRM Group) / Program (CRM Program) to an
account. A rule matches a lead only if EVERY axis it specifies matches; among
matching rules the MOST SPECIFIC wins (Program > Group > Product Line).

There is deliberately **no global default** — an unmatched lead raises at send
time (see message.set_whatsapp_account). We never silently send through the
wrong tenant. A catch-all is possible only by an explicit rule with all axes
blank, if the operator chooses to create one.
"""
import frappe

# Specificity weights — higher = more specific.
_PROGRAM_W, _GROUP_W, _VERTICAL_W = 4, 2, 1


def resolve_account_for_lead(lead):
	"""Return the WhatsApp Account name for a lead, or None if no rule matches."""
	program = lead.get("custom_current_program")
	group = lead.get("custom_psp_group")
	vertical = lead.get("custom_vertical")

	best, best_score = None, -1
	for rule in frappe.get_all(
		"WATI Account Routing",
		fields=["whatsapp_account", "program", "psp_group", "vertical"],
	):
		# Every axis the rule specifies must match the lead.
		if rule.program and rule.program != program:
			continue
		if rule.psp_group and rule.psp_group != group:
			continue
		if rule.vertical and rule.vertical != vertical:
			continue
		score = (
			(_PROGRAM_W if rule.program else 0)
			+ (_GROUP_W if rule.psp_group else 0)
			+ (_VERTICAL_W if rule.vertical else 0)
		)
		if score > best_score:
			best, best_score = rule.whatsapp_account, score
	return best


def resolve_for_message(msg):
	"""Resolve the account for an outgoing WhatsApp Message linked to a CRM Lead."""
	if msg.reference_doctype != "CRM Lead" or not msg.reference_name:
		return None
	lead = frappe.get_cached_doc("CRM Lead", msg.reference_name)
	return resolve_account_for_lead(lead)


def account_for_channel(channel_number):
	"""Inbound: map the WABA number that received the message -> its WhatsApp Account."""
	from tatva_connect.wati import api as wati

	if channel_number:
		digits = wati.normalize_number(channel_number)
		account = frappe.db.get_value(
			"WhatsApp Account", {"custom_wati_channel_number": digits}, "name"
		)
		if account:
			return account
	# Fallback while single-tenant: the one WATI account.
	return frappe.db.get_value("WhatsApp Account", {"custom_is_wati": 1}, "name")
