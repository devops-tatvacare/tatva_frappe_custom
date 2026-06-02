# Copyright (c) 2026, TatvaCare and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class WATIAccountRouting(Document):
	def validate(self):
		# Two rules with the IDENTICAL (vertical, group, program) triple are equally
		# specific and could both match a lead -> ambiguous routing. Block the
		# duplicate at the source so resolution stays deterministic.
		dup = frappe.db.exists(
			"WATI Account Routing",
			{
				"vertical": self.vertical or "",
				"psp_group": self.psp_group or "",
				"program": self.program or "",
				"name": ["!=", self.name],
			},
		)
		if dup:
			frappe.throw(
				_(
					"A routing rule with the same Product Line / Group / Program already "
					"exists ({0}). Each combination must be unique."
				).format(dup),
				title=_("Duplicate routing rule"),
			)
