plugins {
    kotlin("jvm") version "2.0.21"
    kotlin("plugin.serialization") version "2.0.21"
    `maven-publish`
}

group = "com.evpnc"
version = "0.1.0"

repositories { mavenCentral() }

dependencies {
    api("org.jetbrains.kotlinx:kotlinx-serialization-json:1.7.3")
    testImplementation(kotlin("test"))
}

java {
    sourceCompatibility = JavaVersion.VERSION_17
    targetCompatibility = JavaVersion.VERSION_17
}

kotlin {
    compilerOptions { jvmTarget.set(org.jetbrains.kotlin.gradle.dsl.JvmTarget.JVM_17) }
}

tasks.test {
    useJUnitPlatform()
    // Optional: a checkout of the OCPI spec at the pinned commit, for its example files.
    environment("OCPI_SPEC_DIR", System.getenv("OCPI_SPEC_DIR") ?: "")
    systemProperty("repo.root", rootDir.resolve("../..").canonicalPath)
}

publishing {
    publications { create<MavenPublication>("model") { from(components["java"]) } }
}
