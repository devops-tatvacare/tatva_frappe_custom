# Acefone native call UI via clean overrides (no CRM fork)

**Binding rule:** no `frappe/crm` (or any app) source edits. Only `override_whitelisted_methods` + config + our own `tatva_connect` code.

## Idea
crm's native call UI (phone icon on lead/deal/contact, "Make a Call", the call popup, the inline "Listen" recording player) lights up when `callEnabled` is true — i.e. when a telephony integration's settings are enabled. We enable the **Exotel slot** (no Exotel creds needed) and **override the two backend methods** crm's UI calls, so the native UI drives **Acefone** instead. The CRM never reaches Exotel — `make_a_call` is fully replaced.

## Overrides (in `hooks.py`)
| crm method (replaced) | our handler | effect |
|---|---|---|
| `crm.integrations.exotel.handler.make_a_call` | `tatva_connect.acefone.bridge.make_a_call` | native phone icon places an **Acefone bridge call** (account chosen by routing) |
| `crm.fcrm.doctype.crm_call_log.crm_call_log.get_call_log` | `tatva_connect.acefone.bridge.get_call_log` | delegates to crm, then for Acefone calls fills `recording_url_path` with our streaming-proxy URL → the native **"Listen"** player works inline |

`get_call_log` calls the original crm function (imported directly) and only augments — so Twilio/Exotel behaviour is untouched.

## Contract (verified in crm source)
- `ExotelCallUI.makeOutgoingCall` → `make_a_call({to_number})`, `onSuccess(callDetails)` just shows the popup; `onError` shows `err.messages[0]`. So our override: return a small dict on success; `frappe.throw` a clean message on failure (no blank toast).
- `CallArea.vue` shows "Listen" when `recording_url` is set and plays `callLog.data.recording_url_path`.

## Config (no creds)
- Enable **CRM Exotel Settings → Enabled** (the "slot" — turns on `callEnabled`).
- Enable **Acefone Settings → Enabled** (our kill-switch).

## Remove (the spread-out buttons)
- Delete the Acefone CRM Form Script ("Acefone Telephony (CRM Lead)") + `lead_acefone.js` + `api/telephony.list_recordings`. Keep `api/telephony.recording` (the proxy — now used by `get_call_log`).

## Outbound flow
native phone icon → `makeCall(mobile)` → `exotel.makeOutgoingCall` → **our** `make_a_call(to_number)`:
1. resolve lead/deal from the number (`get_contact_by_phone_number`),
2. resolve its Acefone account via routing (no route → clean throw),
3. agent number = caller's `CRM Telephony Agent.acefone_number`, else the account's,
4. create an Initiated `CRM Call Log` (medium=Acefone, account stamped, linked),
5. `click_to_call(..., custom_identifier=call_log.name)`; failure → mark Failed + throw.
The webhook later reconciles the row to its terminal status (existing handler).

## Recordings
Inline in the Calls tab via the native player; streamed on demand through `api/telephony.recording` (no storage). Recording URL is captured from the CDR webhook (`payload.recording_url`) by the existing handler.

## Auto-refresh (open)
crm's Calls tab only auto-refreshes on `whatsapp_message`; there is **no** call socket listener. Refreshing the list after a call cannot be done by a pure backend override. Options without a fork: (a) a small CRM Form Script that listens on our realtime event and soft-reloads, or (b) accept manual reload. Decide after the core lands — will not fork.

## Files
- `tatva_connect/acefone/bridge.py` (new) — the two overrides + small helpers.
- `tatva_connect/hooks.py` — register the two overrides.
- `tatva_connect/acefone/handler.py` — `make_acefone_call` becomes a thin delegate to `bridge`; keep the inbound webhook + `_process` (add a minimal `exotel_call` publish for the popup).
- remove `acefone/form_scripts/lead_acefone.js`; trim `api/telephony.py` to just `recording`.

## Test (dev)
- Phone icon appears on a lead (Exotel slot on).
- Click → Acefone account resolved → Call Log Initiated; no route → clean toast.
- A call with `recording_url` → "Listen" plays via the proxy.
- No header buttons remain.
