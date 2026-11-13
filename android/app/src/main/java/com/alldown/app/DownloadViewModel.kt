package com.alldown.app

import android.app.Application
import android.media.MediaScannerConnection
import android.os.Environment
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.yausername.youtubedl_android.YoutubeDL
import com.yausername.youtubedl_android.YoutubeDLRequest
import com.yausername.youtubedl_android.mapper.VideoInfo
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import java.io.File
import java.util.UUID

enum class MediaFormat(val label: String) {
    MP4("MP4"),
    MKV("MKV"),
    MP3("MP3"),
}

data class QualityOption(
    val label: String,
    val height: Int?,
)

data class DownloadUiState(
    val url: String = "",
    val platform: Platform = Platform.YOUTUBE,
    val isLoggedIn: Boolean = false,
    val isBusy: Boolean = false,
    val isAnalyzing: Boolean = false,
    val statusText: String = "Cole um link do YouTube, Instagram, Facebook ou TikTok",
    val progress: Float = 0f,
    val progressDetail: String = "",
    val videoTitle: String? = null,
    val videoAuthor: String? = null,
    val videoDuration: String? = null,
    val thumbnailUrl: String? = null,
    val qualityOptions: List<QualityOption> = listOf(QualityOption("Melhor disponível (Auto)", null)),
    val selectedQuality: QualityOption = QualityOption("Melhor disponível (Auto)", null),
    val selectedFormat: MediaFormat = MediaFormat.MP4,
    val selectedBitrate: String = "320",
    val errorMessage: String? = null,
    val downloadedFolder: String? = null,
    val showTutorial: Boolean = false,
)

class DownloadViewModel(application: Application) : AndroidViewModel(application) {
    private val _uiState = MutableStateFlow(
        DownloadUiState(
            isLoggedIn = CookieStore.hasValidYoutubeCookies(application)
        )
    )
    val uiState: StateFlow<DownloadUiState> = _uiState.asStateFlow()

    private var currentProcessId: String? = null
    private var lastVideoInfo: VideoInfo? = null

    fun refreshLoginState() {
        val logged = CookieStore.hasValidYoutubeCookies(getApplication())
        _uiState.update { it.copy(isLoggedIn = logged) }
    }

    fun logout() {
        CookieStore.clear(getApplication())
        _uiState.update {
            it.copy(
                isLoggedIn = false,
                statusText = "Sessão do YouTube desconectada"
            )
        }
    }

    fun updateUrl(raw: String) {
        val cleaned = raw.trim()
        _uiState.update {
            it.copy(
                url = cleaned,
                platform = PlatformDetector.detect(cleaned),
                errorMessage = null,
            )
        }
    }

    fun selectFormat(format: MediaFormat) {
        _uiState.update { it.copy(selectedFormat = format) }
    }

    fun selectQuality(option: QualityOption) {
        _uiState.update { it.copy(selectedQuality = option) }
    }

    fun selectBitrate(bitrate: String) {
        _uiState.update { it.copy(selectedBitrate = bitrate) }
    }

    fun setShowTutorial(show: Boolean) {
        _uiState.update { it.copy(showTutorial = show) }
    }

    fun clearError() {
        _uiState.update { it.copy(errorMessage = null) }
    }

    fun cancelDownload() {
        val pid = currentProcessId ?: return
        YoutubeDL.getInstance().destroyProcessById(pid)
        currentProcessId = null
        _uiState.update {
            it.copy(
                isBusy = false,
                isAnalyzing = false,
                statusText = "Download cancelado",
                progress = 0f,
                progressDetail = "",
            )
        }
    }

    private suspend fun waitForEngine(): Boolean {
        val app = getApplication<AllDownApp>()
        var attempts = 0
        while (!app.isEngineReady && app.engineInitError == null && attempts < 100) {
            delay(150)
            attempts++
        }
        if (app.engineInitError != null) {
            _uiState.update {
                it.copy(
                    isBusy = false,
                    isAnalyzing = false,
                    errorMessage = app.engineInitError,
                )
            }
            return false
        }
        return app.isEngineReady
    }

    private fun applyCommonOptions(request: YoutubeDLRequest, platform: Platform) {
        request.addOption("--no-playlist")
        request.addOption("--retries", "10")
        request.addOption("--fragment-retries", "10")
        request.addOption("--socket-timeout", "30")
        request.addOption("--http-chunk-size", "10485760")
        request.addOption("--continue")

        val cookieFile = CookieStore.cookieFile(getApplication())
        if (cookieFile.isFile && cookieFile.length() > 0L) {
            request.addOption("--cookies", cookieFile.absolutePath)
        }

        if (platform != Platform.YOUTUBE) {
            request.addOption(
                "--user-agent",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
            )
        }
    }

    fun analyze() {
        val url = _uiState.value.url.trim()
        if (url.isEmpty() || _uiState.value.isBusy) return
        val platform = PlatformDetector.detect(url)

        viewModelScope.launch(Dispatchers.IO) {
            _uiState.update {
                it.copy(
                    isBusy = true,
                    isAnalyzing = true,
                    platform = platform,
                    statusText = "Analisando link (${platform.label})…",
                    errorMessage = null,
                    downloadedFolder = null,
                    progress = 0f,
                    progressDetail = "",
                )
            }

            if (!waitForEngine()) return@launch

            try {
                val request = YoutubeDLRequest(url)
                applyCommonOptions(request, platform)
                val info = YoutubeDL.getInstance().getInfo(request)
                lastVideoInfo = info

                val heights = (info.formats ?: emptyList())
                    .mapNotNull { it.height }
                    .filter { it > 0 }
                    .distinct()
                    .sortedDescending()

                val options = mutableListOf(QualityOption("Melhor disponível (Auto)", null))
                heights.forEach { h ->
                    val tag = when {
                        h >= 2160 -> "${h}p (4K)"
                        h >= 1440 -> "${h}p (2K)"
                        h >= 1080 -> "${h}p (Full HD)"
                        h >= 720 -> "${h}p (HD)"
                        else -> "${h}p"
                    }
                    options.add(QualityOption(tag, h))
                }

                _uiState.update {
                    it.copy(
                        isBusy = false,
                        isAnalyzing = false,
                        videoTitle = info.title ?: "Sem título",
                        videoAuthor = info.uploader ?: info.channel ?: platform.label,
                        videoDuration = formatDuration(info.duration),
                        thumbnailUrl = info.thumbnail,
                        qualityOptions = options,
                        selectedQuality = if (options.size > 1) options[1] else options[0],
                        statusText = "Pronto para baixar",
                    )
                }
            } catch (e: Exception) {
                _uiState.update {
                    it.copy(
                        isBusy = false,
                        isAnalyzing = false,
                        statusText = "Falha na análise",
                        errorMessage = e.localizedMessage ?: "Não foi possível analisar este link",
                    )
                }
            }
        }
    }

    fun download() {
        val state = _uiState.value
        if (state.isBusy || state.url.isBlank()) return
        val platform = state.platform

        viewModelScope.launch(Dispatchers.IO) {
            _uiState.update {
                it.copy(
                    isBusy = true,
                    isAnalyzing = false,
                    statusText = "Iniciando download…",
                    progress = 0f,
                    progressDetail = "",
                    errorMessage = null,
                    downloadedFolder = null,
                )
            }

            if (!waitForEngine()) return@launch

            val downloadsRoot = Environment.getExternalStoragePublicDirectory(Environment.DIRECTORY_DOWNLOADS)
            val targetDir = File(downloadsRoot, "AllDown").apply { mkdirs() }
            val pid = UUID.randomUUID().toString()
            currentProcessId = pid

            try {
                val request = YoutubeDLRequest(state.url)
                applyCommonOptions(request, platform)
                request.addOption("-o", "${targetDir.absolutePath}/%(title).120B.%(ext)s")
                request.addOption("--restrict-filenames")

                if (state.selectedFormat == MediaFormat.MP3) {
                    request.addOption("-x")
                    request.addOption("--audio-format", "mp3")
                    request.addOption("--audio-quality", state.selectedBitrate)
                    request.addOption("--embed-metadata")
                } else {
                    val h = state.selectedQuality.height
                    val fmt = if (h == null) {
                        "bv*+ba/b"
                    } else if (state.selectedFormat == MediaFormat.MP4) {
                        "bv*[height=$h]+ba[ext=m4a]/bv*[height=$h]+ba/b[height=$h]/bv*[height<=$h]+ba/b"
                    } else {
                        "bv*[height=$h]+ba/b[height=$h]/bv*[height<=$h]+ba/b"
                    }
                    request.addOption("-f", fmt)
                    request.addOption("--merge-output-format", state.selectedFormat.name.lowercase())
                }

                YoutubeDL.getInstance().execute(request, pid) { progress, etaInSeconds, line ->
                    val pct = (progress.coerceIn(0f, 100f)) / 100f
                    val detail = if (etaInSeconds >= 0) {
                        "${progress.toInt()}% • ETA ${etaInSeconds}s"
                    } else {
                        line.take(48)
                    }
                    _uiState.update {
                        it.copy(
                            progress = pct,
                            progressDetail = detail,
                            statusText = "Baixando (${state.selectedFormat.label})…",
                        )
                    }
                }

                currentProcessId = null
                targetDir.listFiles()?.forEach { file ->
                    MediaScannerConnection.scanFile(
                        getApplication(),
                        arrayOf(file.absolutePath),
                        null,
                        null
                    )
                }

                _uiState.update {
                    it.copy(
                        isBusy = false,
                        progress = 1f,
                        statusText = "Concluído! Salvo em Downloads/AllDown",
                        progressDetail = "100%",
                        downloadedFolder = targetDir.absolutePath,
                    )
                }
            } catch (e: Exception) {
                currentProcessId = null
                _uiState.update {
                    it.copy(
                        isBusy = false,
                        statusText = "Erro no download",
                        errorMessage = e.localizedMessage ?: "Falha ao baixar",
                    )
                }
            }
        }
    }

    private fun formatDuration(seconds: Int): String {
        if (seconds <= 0) return "--:--"
        val h = seconds / 3600
        val m = (seconds % 3600) / 60
        val s = seconds % 60
        return if (h > 0) "%d:%02d:%02d".format(h, m, s) else "%02d:%02d".format(m, s)
    }
}
