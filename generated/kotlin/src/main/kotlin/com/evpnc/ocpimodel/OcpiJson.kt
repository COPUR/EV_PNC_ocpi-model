package com.evpnc.ocpimodel

import kotlinx.serialization.json.Json

/**
 * The JSON configuration every EV_PNC service should use with these types: unknown fields are
 * ignored (OCPI peers may add fields), absent optional fields stay null and are not written,
 * and defaults such as `event_type` are written.
 */
val OcpiJson: Json = Json {
    ignoreUnknownKeys = true
    explicitNulls = false
    encodeDefaults = true
}
