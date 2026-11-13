package com.alldown.app

import androidx.compose.ui.graphics.Color

enum class Platform(
    val label: String,
    val badgeColor: Color,
) {
    YOUTUBE("YouTube", Color(0xFFE50914)),
    INSTAGRAM("Instagram", Color(0xFFE1306C)),
    FACEBOOK("Facebook", Color(0xFF1877F2)),
    TIKTOK("TikTok", Color(0xFF0D9488)),
    OTHER("Web", Color(0xFF2563EB)),
}

object PlatformDetector {
    fun detect(url: String): Platform {
        val lower = url.lowercase()
        return when {
            "youtube.com" in lower || "youtu.be" in lower -> Platform.YOUTUBE
            "instagram.com" in lower || "instagr.am" in lower -> Platform.INSTAGRAM
            "facebook.com" in lower || "fb.watch" in lower || "fb.com" in lower -> Platform.FACEBOOK
            "tiktok.com" in lower -> Platform.TIKTOK
            else -> Platform.OTHER
        }
    }

    fun extractFirstUrl(text: String): String {
        val regex = Regex("""https?://\S+""")
        return regex.find(text)?.value ?: text.trim()
    }
}
