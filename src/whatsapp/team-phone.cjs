'use strict';

// WhatsApp, TEAM_PHONE mode only. Builds the message object; it never opens a network connection.
const { validateWhatsAppMessage } = require('../contracts/index.cjs');

function buildTeamPhoneMessage({ displayLabel, text, idempotencyKey, toNumber, teamPhones }) {
  if (!Array.isArray(teamPhones) || !teamPhones.includes(toNumber)) {
    throw new Error('Refused: WhatsApp messages may only go to team phones (TEAM_PHONE mode).');
  }
  const message = Object.freeze({
    display_label: displayLabel,
    direction: 'outbound',
    text,
    idempotency_key: idempotencyKey,
    mode: 'TEAM_PHONE',
    label: 'TEAM_PHONE',
  });
  const check = validateWhatsAppMessage(message);
  if (!check.valid) throw new Error(`Invalid WhatsApp message: ${check.errors.join('; ')}`);
  return message;
}

module.exports = { buildTeamPhoneMessage };
