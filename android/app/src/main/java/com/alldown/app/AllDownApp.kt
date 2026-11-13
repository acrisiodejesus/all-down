package com.alldown.app

import android.app.Application
import com.yausername.ffmpeg.FFmpeg
import com.yausername.youtubedl_android.YoutubeDL
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.launch

class AllDownApp : Application() {
    private val appScope = CoroutineScope(SupervisorJob() + Dispatchers.IO)

    @Volatile
    var isEngineReady: Boolean = false
        private set

    @Volatile
    var engineInitError: String? = null
        private set

    override fun onCreate() {
        super.onCreate()
        appScope.launch {
            try {
                YoutubeDL.getInstance().init(this@AllDownApp)
                FFmpeg.getInstance().init(this@AllDownApp)
                isEngineReady = true
            } catch (e: Exception) {
                engineInitError = e.localizedMessage ?: "Erro ao inicializar motor de download"
            }
        }
    }
}
