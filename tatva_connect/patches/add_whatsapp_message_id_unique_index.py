"""Add a unique index on `WhatsApp Message.message_id`.

Inbound ingest and status threading both key on message_id. Without a DB-level
unique constraint, two workers processing the same redelivered WATI webhook can
both pass the application-level `exists()` check and insert duplicate rows. A
unique index closes that race (MySQL/MariaDB allow multiple NULLs, so rows
without a message_id — e.g. drafts — are unaffected).

Defensive: if legacy duplicate message_ids already exist the index can't be
created; we log and skip rather than abort `bench migrate`.
"""
import frappe


def execute():
	table = "tabWhatsApp Message"
	index_name = "message_id_unique"

	existing = frappe.db.sql(
		f"SHOW INDEX FROM `{table}` WHERE Key_name = %s", index_name
	)
	if existing:
		return

	dupes = frappe.db.sql(
		f"""
		SELECT message_id FROM `{table}`
		WHERE message_id IS NOT NULL AND message_id != ''
		GROUP BY message_id HAVING COUNT(*) > 1 LIMIT 1
		"""
	)
	if dupes:
		frappe.log_error(
			title="WATI: message_id unique index skipped",
			message=(
				"Duplicate message_id values exist on WhatsApp Message; the unique "
				"index was not created. De-duplicate, then re-run this patch."
			),
		)
		return

	try:
		frappe.db.sql(
			f"ALTER TABLE `{table}` ADD UNIQUE INDEX `{index_name}` (`message_id`)"
		)
	except Exception:
		frappe.log_error(
			title="WATI: message_id unique index failed",
			message=frappe.get_traceback(),
		)
