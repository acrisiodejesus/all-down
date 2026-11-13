package com.alldown.app

import android.content.Context
import android.webkit.CookieManager
import java.io.File

object CookieStore {
    private val authCookieNames = setOf(
        "SID", "HSID", "SSID", "APISID", "SAPISID",
        "__Secure-1PSID", "__Secure-3PSID", "LOGIN_INFO"
    )

    private val targetDomains = listOf(
        ".youtube.com" to "https://www.youtube.com",
        ".google.com" to "https://accounts.google.com",
        ".youtu.be" to "https://youtu.be",
    )

    fun cookieFile(context: Context): File = File(context.filesDir, "cookies.txt")

    fun hasValidYoutubeCookies(context: Context): Boolean {
        val file = cookieFile(context)
        if (!file.isFile || file.length() == 0L) return false
        val text = file.readText()
        return authCookieNames.any { name -> text.contains("\t$name\t") }
    }

    fun exportFromWebView(context: Context): Boolean {
        val manager = CookieManager.getInstance()
        manager.flush()
        val lines = mutableListOf("# Netscape HTTP Cookie File")
        val seen = mutableSetOf<String>()
        val expiry = (System.currentTimeMillis() / 1000L) + 365L * 24L * 3600L

        for ((domain, url) in targetDomains) {
            val raw = manager.getCookie(url).orEmpty()
            if (raw.isBlank()) continue
            raw.split(";").forEach { pair ->
                val idx = pair.indexOf('=')
                if (idx <= 0) return@forEach
                val name = pair.substring(0, idx).trim()
                val value = pair.substring(idx + 1).trim()
                val key = "$domain|$name"
                if (name.isNotEmpty() && seen.add(key)) {
                    val secure = if (name.startsWith("__Secure-") || name.startsWith("__Host-")) "TRUE" else "FALSE"
                    lines.add("$domain\tTRUE\t/\t$secure\t$expiry\t$name\t$value")
                }
            }
        }

        val file = cookieFile(context)
        file.writeText(lines.joinToString("\n") + "\n")
        return hasValidYoutubeCookies(context)
    }

    fun clear(context: Context) {
        cookieFile(context).delete()
        CookieManager.getInstance().removeAllCookies(null)
        CookieManager.getInstance().flush()
    }
}
