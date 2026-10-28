package com.evpnc.ocpimodel

import java.io.File
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertTrue
import kotlinx.serialization.KSerializer
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonElement
import kotlinx.serialization.serializer

/** Same fixtures and spec examples as generated/python/tests, parsed by the Kotlin types. */
class ConformanceTest {
    private val repo = File(System.getProperty("repo.root"))

    private fun json(file: File): JsonElement = Json.parseToJsonElement(file.readText())

    private inline fun <reified T> roundTrip(file: File) {
        val serializer: KSerializer<T> = serializer()
        val original = json(file)
        val parsed = OcpiJson.decodeFromJsonElement(serializer, original)
        assertEquals(original, OcpiJson.encodeToJsonElement(serializer, parsed), file.name)
    }

    @Test
    fun eventFixturesRoundTrip() {
        roundTrip<TokenAuthorizeRequested>(repo.resolve("examples/events/token-authorize-requested.json"))
        roundTrip<TokenAuthorizeDecided>(repo.resolve("examples/events/token-authorize-decided.json"))
        roundTrip<SessionStarted>(repo.resolve("examples/events/session-started.json"))
        roundTrip<SessionUpdated>(repo.resolve("examples/events/session-updated.json"))
        roundTrip<SessionEnded>(repo.resolve("examples/events/session-ended.json"))
        roundTrip<CdrReceived>(repo.resolve("examples/events/cdr-received.json"))
        roundTrip<GrantChanged>(repo.resolve("examples/events/grant-changed.json"))
    }

    @Test
    fun ocpiFixturesRoundTrip() {
        roundTrip<Session>(repo.resolve("examples/ocpi/session.json"))
        roundTrip<CDR>(repo.resolve("examples/ocpi/cdr-with-extension.json"))
    }

    @Test
    fun eventTypeDefaultIsWritten() {
        val ev = OcpiJson.decodeFromString<GrantChanged>(
            """{"event_id":"e","event_type":"GrantChanged","schema_version":"0.1.0","occurred_at":"2026-11-02T09:15:00Z","producer":"p",
               "grant_id":"g","subject_ref":"s","purpose":"x","change":"GRANTED","effective_at":"2026-11-02T10:00:00Z"}""",
        )
        assertTrue(OcpiJson.encodeToString(GrantChanged.serializer(), ev).contains("\"event_type\":\"GrantChanged\""))
    }

    @Test
    fun specExamplesParse() {
        val spec = System.getenv("OCPI_SPEC_DIR")?.takeIf { it.isNotBlank() } ?: return
        // Four spec examples disagree with the spec's own tables; python/tests lists why.
        val knownBad = setOf(
            "cdr_example.json",
            "tariff_put_example.json",
            "location_example.json",
            "location_example_parking_garage_opening_hours.json",
        )
        val dir = File(spec, "examples")
        var parsed = 0
        fun each(prefix: String, block: (File) -> Unit) = dir.listFiles { f -> f.name.startsWith(prefix) && f.extension == "json" }!!
            .sortedBy { it.name }.filter { it.name !in knownBad }.forEach { block(it); parsed++ }
        each("session_example") { OcpiJson.decodeFromString<Session>(it.readText()) }
        each("tariff_") { OcpiJson.decodeFromString<Tariff>(it.readText()) }
        each("token_example") { OcpiJson.decodeFromString<Token>(it.readText()) }
        each("token_put") { OcpiJson.decodeFromString<Token>(it.readText()) }
        each("location_example") { OcpiJson.decodeFromString<Location>(it.readText()) }
        each("credentials_example") { OcpiJson.decodeFromString<Credentials>(it.readText()) }
        assertTrue(parsed >= 30, "expected at least 30 spec examples, parsed $parsed")
    }
}
