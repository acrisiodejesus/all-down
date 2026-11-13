package com.alldown.app

import android.Manifest
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Build
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.compose.setContent
import androidx.activity.result.contract.ActivityResultContracts
import androidx.activity.viewModels
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Close
import androidx.compose.material.icons.filled.ContentPaste
import androidx.compose.material.icons.filled.Download
import androidx.compose.material.icons.filled.HelpOutline
import androidx.compose.material.icons.filled.Key
import androidx.compose.material.icons.filled.Search
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.DropdownMenu
import androidx.compose.material3.DropdownMenuItem
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.OutlinedTextFieldDefaults
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.darkColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalClipboardManager
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.core.content.ContextCompat
import coil.compose.AsyncImage

private val BgColor = Color(0xFF0B0F19)
private val CardColor = Color(0xFF131A2A)
private val BorderColor = Color(0xFF232D42)
private val AccentRed = Color(0xFFE50914)
private val TextPrimary = Color(0xFFF8FAFC)
private val TextMuted = Color(0xFF94A3B8)

class MainActivity : ComponentActivity() {
    private val viewModel: DownloadViewModel by viewModels()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        handleIncomingIntent(intent)

        setContent {
            MaterialTheme(
                colorScheme = darkColorScheme(
                    background = BgColor,
                    surface = CardColor,
                    primary = AccentRed,
                    onPrimary = Color.White,
                )
            ) {
                AllDownScreen(viewModel)
            }
        }
    }

    override fun onNewIntent(intent: Intent) {
        super.onNewIntent(intent)
        handleIncomingIntent(intent)
    }

    private fun handleIncomingIntent(intent: Intent?) {
        if (intent?.action == Intent.ACTION_SEND && intent.type == "text/plain") {
            val shared = intent.getStringExtra(Intent.EXTRA_TEXT) ?: return
            val url = PlatformDetector.extractFirstUrl(shared)
            viewModel.updateUrl(url)
            viewModel.analyze()
        }
    }
}

@Composable
fun AllDownScreen(viewModel: DownloadViewModel) {
    val state by viewModel.uiState.collectAsState()
    val context = LocalContext.current
    val clipboard = LocalClipboardManager.current

    val loginLauncher = rememberLauncherForActivityResult(
        ActivityResultContracts.StartActivityForResult()
    ) {
        viewModel.refreshLoginState()
    }

    val storagePermLauncher = rememberLauncherForActivityResult(
        ActivityResultContracts.RequestPermission()
    ) { }

    LaunchedEffect(Unit) {
        if (Build.VERSION.SDK_INT <= Build.VERSION_CODES.P) {
            val granted = ContextCompat.checkSelfPermission(
                context,
                Manifest.permission.WRITE_EXTERNAL_STORAGE
            ) == PackageManager.PERMISSION_GRANTED
            if (!granted) {
                storagePermLauncher.launch(Manifest.permission.WRITE_EXTERNAL_STORAGE)
            }
        }
    }

    Scaffold(
        containerColor = BgColor
    ) { padding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .verticalScroll(rememberScrollState())
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(14.dp),
        ) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Column {
                    Text(
                        text = "ALL DOWN",
                        color = TextPrimary,
                        fontSize = 24.sp,
                        fontWeight = FontWeight.Bold,
                    )
                    Text(
                        text = "YouTube • Instagram • Facebook • TikTok",
                        color = TextMuted,
                        fontSize = 12.sp,
                    )
                }
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    IconButton(onClick = { viewModel.setShowTutorial(true) }) {
                        Icon(Icons.Default.HelpOutline, contentDescription = "Tutorial", tint = TextPrimary)
                    }
                    OutlinedButton(
                        onClick = {
                            if (state.isLoggedIn) {
                                viewModel.logout()
                            } else {
                                loginLauncher.launch(Intent(context, LoginActivity::class.java))
                            }
                        }
                    ) {
                        Icon(
                            Icons.Default.Key,
                            contentDescription = null,
                            tint = if (state.isLoggedIn) Color(0xFF10B981) else AccentRed,
                            modifier = Modifier.size(16.dp)
                        )
                        Spacer(Modifier.width(6.dp))
                        Text(
                            text = if (state.isLoggedIn) "Conectado" else "Login YT",
                            color = if (state.isLoggedIn) Color(0xFF10B981) else TextPrimary,
                            fontSize = 12.sp,
                        )
                    }
                }
            }

            Card(
                colors = CardDefaults.cardColors(containerColor = CardColor),
                shape = RoundedCornerShape(14.dp),
                modifier = Modifier
                    .fillMaxWidth()
                    .border(1.dp, BorderColor, RoundedCornerShape(14.dp)),
            ) {
                Column(
                    modifier = Modifier.padding(14.dp),
                    verticalArrangement = Arrangement.spacedBy(10.dp),
                ) {
                    OutlinedTextField(
                        value = state.url,
                        onValueChange = { viewModel.updateUrl(it) },
                        placeholder = { Text("Cole o link do vídeo ou Reel...", color = TextMuted) },
                        singleLine = true,
                        modifier = Modifier.fillMaxWidth(),
                        colors = OutlinedTextFieldDefaults.colors(
                            focusedBorderColor = AccentRed,
                            unfocusedBorderColor = BorderColor,
                            focusedTextColor = TextPrimary,
                            unfocusedTextColor = TextPrimary,
                        ),
                        trailingIcon = {
                            if (state.url.isNotEmpty()) {
                                IconButton(onClick = { viewModel.updateUrl("") }) {
                                    Icon(Icons.Default.Close, contentDescription = "Limpar", tint = TextMuted)
                                }
                            }
                        }
                    )

                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.spacedBy(8.dp),
                    ) {
                        OutlinedButton(
                            onClick = {
                                val text = clipboard.getText()?.text.orEmpty()
                                if (text.isNotBlank()) {
                                    viewModel.updateUrl(PlatformDetector.extractFirstUrl(text))
                                }
                            },
                            modifier = Modifier.weight(1f),
                        ) {
                            Icon(Icons.Default.ContentPaste, contentDescription = null, modifier = Modifier.size(16.dp))
                            Spacer(Modifier.width(6.dp))
                            Text("Colar")
                        }
                        Button(
                            onClick = { viewModel.analyze() },
                            enabled = !state.isBusy && state.url.isNotBlank(),
                            colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF2563EB)),
                            modifier = Modifier.weight(1.4f),
                        ) {
                            Icon(Icons.Default.Search, contentDescription = null, modifier = Modifier.size(16.dp))
                            Spacer(Modifier.width(6.dp))
                            Text("Analisar")
                        }
                    }
                }
            }

            if (state.videoTitle != null) {
                Card(
                    colors = CardDefaults.cardColors(containerColor = CardColor),
                    shape = RoundedCornerShape(14.dp),
                    modifier = Modifier
                        .fillMaxWidth()
                        .border(1.dp, BorderColor, RoundedCornerShape(14.dp)),
                ) {
                    Column(
                        modifier = Modifier.padding(14.dp),
                        verticalArrangement = Arrangement.spacedBy(10.dp),
                    ) {
                        Row(
                            horizontalArrangement = Arrangement.spacedBy(12.dp),
                            verticalAlignment = Alignment.CenterVertically,
                        ) {
                            AsyncImage(
                                model = state.thumbnailUrl,
                                contentDescription = "Thumbnail",
                                contentScale = ContentScale.Crop,
                                modifier = Modifier
                                    .size(width = 120.dp, height = 68.dp)
                                    .clip(RoundedCornerShape(8.dp))
                                    .background(Color(0xFF1E293B)),
                            )
                            Column(modifier = Modifier.weight(1f)) {
                                Surface(
                                    color = state.platform.badgeColor,
                                    shape = RoundedCornerShape(6.dp),
                                ) {
                                    Text(
                                        text = state.platform.label.uppercase(),
                                        color = Color.White,
                                        fontSize = 10.sp,
                                        fontWeight = FontWeight.Bold,
                                        modifier = Modifier.padding(horizontal = 6.dp, vertical = 2.dp),
                                    )
                                }
                                Spacer(Modifier.height(4.dp))
                                Text(
                                    text = state.videoTitle.orEmpty(),
                                    color = TextPrimary,
                                    fontSize = 14.sp,
                                    fontWeight = FontWeight.SemiBold,
                                    maxLines = 2,
                                    overflow = TextOverflow.Ellipsis,
                                )
                                Text(
                                    text = "${state.videoAuthor} • ${state.videoDuration}",
                                    color = TextMuted,
                                    fontSize = 12.sp,
                                )
                            }
                        }

                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.spacedBy(8.dp),
                        ) {
                            MediaFormat.entries.forEach { fmt ->
                                val selected = state.selectedFormat == fmt
                                Box(
                                    modifier = Modifier
                                        .weight(1f)
                                        .clip(RoundedCornerShape(8.dp))
                                        .background(if (selected) AccentRed else Color(0xFF1E293B))
                                        .clickable { viewModel.selectFormat(fmt) }
                                        .padding(vertical = 10.dp),
                                    contentAlignment = Alignment.Center,
                                ) {
                                    Text(
                                        text = fmt.label,
                                        color = Color.White,
                                        fontWeight = FontWeight.Bold,
                                        fontSize = 13.sp,
                                    )
                                }
                            }
                        }

                        if (state.selectedFormat == MediaFormat.MP3) {
                            BitrateDropdown(
                                selected = state.selectedBitrate,
                                onSelect = { viewModel.selectBitrate(it) },
                            )
                        } else {
                            QualityDropdown(
                                options = state.qualityOptions,
                                selected = state.selectedQuality,
                                onSelect = { viewModel.selectQuality(it) },
                            )
                        }

                        Button(
                            onClick = { viewModel.download() },
                            enabled = !state.isBusy,
                            colors = ButtonDefaults.buttonColors(containerColor = AccentRed),
                            modifier = Modifier
                                .fillMaxWidth()
                                .height(48.dp),
                        ) {
                            Icon(Icons.Default.Download, contentDescription = null)
                            Spacer(Modifier.width(8.dp))
                            Text(
                                text = if (state.selectedFormat == MediaFormat.MP3) "BAIXAR ÁUDIO (MP3)" else "BAIXAR VÍDEO",
                                fontWeight = FontWeight.Bold,
                            )
                        }
                    }
                }
            }

            Card(
                colors = CardDefaults.cardColors(containerColor = CardColor),
                shape = RoundedCornerShape(14.dp),
                modifier = Modifier
                    .fillMaxWidth()
                    .border(1.dp, BorderColor, RoundedCornerShape(14.dp)),
            ) {
                Column(
                    modifier = Modifier.padding(14.dp),
                    verticalArrangement = Arrangement.spacedBy(8.dp),
                ) {
                    Text(text = state.statusText, color = TextPrimary, fontSize = 13.sp)
                    if (state.isBusy || state.progress > 0f) {
                        if (state.isAnalyzing) {
                            LinearProgressIndicator(
                                modifier = Modifier.fillMaxWidth(),
                                color = AccentRed,
                                trackColor = Color(0xFF1E293B),
                            )
                        } else {
                            LinearProgressIndicator(
                                progress = { state.progress },
                                modifier = Modifier.fillMaxWidth(),
                                color = AccentRed,
                                trackColor = Color(0xFF1E293B),
                            )
                        }
                    }
                    if (state.progressDetail.isNotEmpty()) {
                        Text(text = state.progressDetail, color = TextMuted, fontSize = 12.sp)
                    }
                    if (state.isBusy) {
                        OutlinedButton(
                            onClick = { viewModel.cancelDownload() },
                            modifier = Modifier.fillMaxWidth(),
                        ) {
                            Text("Cancelar", color = AccentRed)
                        }
                    }
                }
            }
        }
    }

    if (state.errorMessage != null) {
        AlertDialog(
            onDismissRequest = { viewModel.clearError() },
            containerColor = CardColor,
            title = { Text("All Down", color = TextPrimary) },
            text = { Text(state.errorMessage.orEmpty(), color = TextMuted) },
            confirmButton = {
                TextButton(onClick = { viewModel.clearError() }) {
                    Text("OK", color = AccentRed)
                }
            }
        )
    }

    if (state.showTutorial) {
        AlertDialog(
            onDismissRequest = { viewModel.setShowTutorial(false) },
            containerColor = CardColor,
            title = { Text("Como usar o All Down", color = TextPrimary) },
            text = {
                Text(
                    "1. No YouTube, Instagram, Facebook ou TikTok, toque em Compartilhar > All Down (ou cole o link).\n\n" +
                        "2. Para vídeos do YouTube sem bloqueios, faça login tocando em 'Login YT'.\n\n" +
                        "3. Escolha MP4, MKV ou MP3 e toque em Baixar.\n\n" +
                        "4. Os arquivos ficam salvos na pasta Downloads/AllDown do seu celular.",
                    color = TextMuted,
                    fontSize = 13.sp,
                )
            },
            confirmButton = {
                TextButton(onClick = { viewModel.setShowTutorial(false) }) {
                    Text("Entendi", color = AccentRed)
                }
            }
        )
    }
}

@Composable
private fun QualityDropdown(
    options: List<QualityOption>,
    selected: QualityOption,
    onSelect: (QualityOption) -> Unit,
) {
    var expanded by remember { mutableStateOf(false) }
    Box(modifier = Modifier.fillMaxWidth()) {
        OutlinedButton(
            onClick = { expanded = true },
            modifier = Modifier.fillMaxWidth(),
        ) {
            Text("Qualidade: ${selected.label}", color = TextPrimary)
        }
        DropdownMenu(
            expanded = expanded,
            onDismissRequest = { expanded = false },
            modifier = Modifier.background(CardColor),
        ) {
            options.forEach { opt ->
                DropdownMenuItem(
                    text = { Text(opt.label, color = TextPrimary) },
                    onClick = {
                        onSelect(opt)
                        expanded = false
                    }
                )
            }
        }
    }
}

@Composable
private fun BitrateDropdown(
    selected: String,
    onSelect: (String) -> Unit,
) {
    var expanded by remember { mutableStateOf(false) }
    val options = listOf("320", "256", "192", "128")
    Box(modifier = Modifier.fillMaxWidth()) {
        OutlinedButton(
            onClick = { expanded = true },
            modifier = Modifier.fillMaxWidth(),
        ) {
            Text("Áudio MP3: $selected kbps", color = TextPrimary)
        }
        DropdownMenu(
            expanded = expanded,
            onDismissRequest = { expanded = false },
            modifier = Modifier.background(CardColor),
        ) {
            options.forEach { br ->
                DropdownMenuItem(
                    text = { Text("$br kbps", color = TextPrimary) },
                    onClick = {
                        onSelect(br)
                        expanded = false
                    }
                )
            }
        }
    }
}
