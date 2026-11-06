'use strict';

// WhatsApp client module.
// Guards: refuses to run unless mode is TEAM_PHONE or SIMULATED.
// Asserts no outbound network call to any unlisted number.
const { validateWhatsAppMessage } = require('../contracts/index.cjs');

const ALLOWED_MODES = Object.freeze(['TEAM_PHONE', 'SIMULATED']);

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

function buildSimulatedWhatsAppMessage({ displayLabel, text, idempotencyKey }) {
  const message = Object.freeze({
    display_label: displayLabel,
    direction: 'outbound',
    text,
    idempotency_key: idempotencyKey,
    mode: 'SIMULATED',
    label: 'SIMULATED',
  });
  const check = validateWhatsAppMessage(message);
  if (!check.valid) throw new Error(`Invalid WhatsApp message: ${check.errors.join('; ')}`);
  return message;
}

function createWhatsAppSender({ mode = 'SIMULATED', teamPhones = [] } = {}) {
  if (!ALLOWED_MODES.includes(mode)) {
    throw new Error(`Refused: WhatsApp module refuses to run unless mode is TEAM_PHONE or SIMULATED (received: "${mode}").`);
  }

  const sentRecords = new Map();
  const rawNetworkCallLog = [];

  function send({ displayLabel, text, idempotencyKey, toNumber }) {
    if (!idempotencyKey || typeof idempotencyKey !== 'string') {
      throw new TypeError('idempotencyKey is required and must be a string');
    }

    // Idempotency check: repeated send with the same key returns the existing record
    if (sentRecords.has(idempotencyKey)) {
      const existing = sentRecords.get(idempotencyKey);
      return {
        success: true,
        replayed: true,
        send_count: 1,
        message: existing.message,
      };
    }

    let message;
    if (mode === 'TEAM_PHONE') {
      if (!toNumber || !teamPhones.includes(toNumber)) {
        throw new Error('Refused: WhatsApp messages may only go to team phones (TEAM_PHONE mode).');
      }
      message = buildTeamPhoneMessage({
        displayLabel,
        text,
        idempotencyKey,
        toNumber,
        teamPhones,
      });
      // In TEAM_PHONE mode, only team phones are ever contacted
      rawNetworkCallLog.push({ toNumber, timestamp: new Date().toISOString() });
    } else {
      // SIMULATED mode: strictly simulated, zero network call
      message = buildSimulatedWhatsAppMessage({
        displayLabel,
        text,
        idempotencyKey,
      });
    }

    const record = {
      success: true,
      replayed: false,
      send_count: 1,
      message,
    };
    sentRecords.set(idempotencyKey, record);
    return record;
  }

  return {
    mode,
    send,
    getSentRecords: () => Array.from(sentRecords.values()),
    getRawNetworkCallLog: () => [...rawNetworkCallLog],
  };
}

module.exports = {
  buildTeamPhoneMessage,
  buildSimulatedWhatsAppMessage,
  createWhatsAppSender,
};
