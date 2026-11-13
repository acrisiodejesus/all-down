# All Down — Downloader Universal 4K/8K (YouTube, Instagram, Facebook & TikTok)

[![Download All Down Portable](https://img.shields.io/badge/Download-All%20Down%20Port%C3%A1til-E50914?style=for-the-badge&logo=windows&logoColor=white)](https://github.com/acrisiodejesus/all-down/releases/latest/download/AllDown-Portable.zip)
[![GitHub Releases](https://img.shields.io/badge/Todas%20as%20Vers%C3%B5es-Releases-24292e?style=for-the-badge&logo=github)](https://github.com/acrisiodejesus/all-down/releases)

### 📦 Download da Versão Portátil (Pronta para Usar)

> ⬇️ **[Baixar AllDown-Portable.zip (Versão mais recente)](https://github.com/acrisiodejesus/all-down/releases/latest/download/AllDown-Portable.zip)**
> 
> - **Nenhuma instalação necessária**: não precisa instalar Python, Node.js ou FFmpeg.
> - **Tudo incluso**: FFmpeg, gerador de PO Token e interface gráfica já vêm embutidos.
> - Basta baixar o arquivo `.zip`, extrair em qualquer pasta e dar um duplo clique em **`AllDown.exe`**.

---

All Down é uma aplicação desktop moderna para Windows desenvolvida para realizar downloads de vídeos, reels, playlists e áudios do **YouTube, Instagram, Facebook e TikTok** na resolução máxima disponível (até 4K Ultra HD e 8K no YouTube), contornando as restrições recentes de PO Token (Proof of Origin), n-sig challenges e rate-limiting.

---

## Recursos

- **Suporte Multi-Plataforma**: Baixe vídeos, Reels, Shorts, Stories públicos e áudios do **YouTube, Instagram, Facebook e TikTok** com detecção automática de plataforma.
- **Resoluções Ultra HD**: Download e detecção automática de resoluções de 360p até 4K (2160p) e 8K (4320p).
- **Download de Playlists Completas**: Baixe playlists inteiras de vídeos ou áudios em lote com um clique, organizadas automaticamente em pastas próprias com numeração sequencial.
- **Download de Áudio em MP3**: Opção para extrair e baixar exclusivamente o áudio em MP3 com taxa de bits configurável (até 320 kbps de máxima fidelidade) e metadados embutidos.
- **Interface Moderna Windows 11**: Interface gráfica moderna com CustomTkinter em modo Dark, cantos arredondados e layout em cartões.
- **Prévia do Vídeo / Playlist**: Exibição da thumbnail, título, canal, duração ou quantidade total de faixas/vídeos.
- **Muxing via FFmpeg**: Mesclagem de streams separados de vídeo de alta resolução e áudio em contêineres MP4 ou MKV.
- **Autenticação Anti-Robô Integrada**: Janela de login nativa do Google/YouTube via WebView2 (Edge Chromium) para exportação segura de sessão (`cookies.txt`), sem necessidade de instalar extensões no navegador.
- **Bypass de PO Token (bgutil)**: Integração com gerador dinâmico de GVS PO Tokens em segundo plano via Node.js runtime.
- **Distribuição Portátil**: Executável standalone que pode ser executado em qualquer máquina Windows sem necessidade de instalar Python, Node.js ou FFmpeg.

---

## 📖 Mini Tutorial de Uso

### 1. Abrir o Aplicativo
Dê um duplo clique no executável **`AllDown.exe`** (na versão portátil) ou execute **`run.bat`** (no ambiente de desenvolvimento).

### 2. Conectar sua Conta do YouTube *(Para YouTube)*
- Na primeira inicialização, o aplicativo verifica se você já fez login no YouTube.
- Para links do **YouTube**, clique em **Sim** ou no botão **`🔑 Fazer Login no YouTube`** e entre com sua conta na janela oficial do Google.
- Para links do **Instagram, Facebook e TikTok**, o login do YouTube não é exigido — basta colar o link público!
> *Dica: Fazer login impede bloqueios de robô do YouTube (HTTP 403 Forbidden) e garante o download em 4K/8K com taxa máxima de transferência.*

### 3. Colar o Link do Vídeo, Reel ou Playlist
- Copie o link do YouTube, Instagram (vídeo/Reel), Facebook (vídeo/Reel) ou TikTok.
- No All Down, clique no botão **`📋 Colar`** ou pressione `Ctrl + V` no campo de texto.
- Caso cole o link de um vídeo do YouTube que faça parte de uma playlist, o app perguntará se você prefere baixar a **playlist inteira** ou **apenas o vídeo individual**.

### 4. Analisar o Vídeo ou Playlist
- Clique em **`Analisar Vídeo`** ou pressione `Enter`.
- O aplicativo identificará o conteúdo e exibirá a miniatura, título, canal e o total de vídeos disponíveis.

### 5. Escolher a Qualidade e Formato
- **Formato Final**: Escolha entre:
  - **MP4**: Vídeo com máxima compatibilidade (TVs, smartphones, editores).
  - **MKV**: Vídeo preservando codecs originais de altíssima definição.
  - **MP3**: Baixa **somente o áudio** convertido em MP3.
- **Qualidade Desejada**:
  - Para vídeos/playlists: resoluções alvo (ex: `Melhor disponível`, `4K Ultra HD`, `1080p Full HD`, `720p HD`).
  - Para MP3: taxa de bits (ex: `320 kbps (Máxima Fidelidade)`, `256 kbps`, `192 kbps` ou `128 kbps`).
- **Salvar na Pasta**: O padrão é a sua pasta *Downloads*.
  > *Ao baixar uma playlist, o aplicativo cria automaticamente uma subpasta com o nome da playlist e numera os arquivos (`01 - ...`, `02 - ...`), mantendo seus arquivos perfeitamente organizados.*

### 6. Iniciar o Download
- Clique no botão vermelho de download (ex: **`⬇ BAIXAR PLAYLIST COMPLETA`** ou **`⬇ BAIXAR VÍDEO`**).
- Acompanhe em tempo real o progresso de cada item (ex: `[1/25] Baixando...`), velocidade e tempo estimado.
- Ao terminar, clique em **`📂 Abrir Pasta`** para abrir o explorador de arquivos diretamente na pasta dos arquivos baixados!

---

## Estrutura do Projeto

```text
all-down/
├── assets/
│   ├── icon.ico           # Ícone multi-resolução para Windows
│   └── icon.png           # Ícone vetorial em alta resolução
├── bin/
│   ├── ffmpeg.exe         # Binário FFmpeg para junção de fluxos
│   └── node.exe           # Runtime Node.js para resolução de desafios JS
├── bgutil_provider/       # Provedor e compilador de PO Token (bgutil)
├── app.py                 # Aplicação principal e interface CustomTkinter
├── login.py               # Módulo de autenticação WebView2
├── build_portable.py      # Script de empacotamento com PyInstaller
├── make_icon.py           # Gerador de ícones via Pillow
├── requirements.txt       # Dependências Python
└── run.bat                # Inicializador para ambiente de desenvolvimento
```

---

## Como Executar

### Opção 1: Versão Portátil (Recomendado para usuários finais)

1. Baixe o pacote pelo link no topo do README ou acesse o diretório local `dist/AllDown-Portable/`.
2. Dê um duplo clique em `AllDown.exe`.

### Opção 2: A partir do código-fonte (Desenvolvimento)

1. Certifique-se de possuir Python 3.11+ instalado no Windows.
2. Execute o arquivo `run.bat` para criar o ambiente virtual e instalar as dependências automaticamente, ou execute manualmente:

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

---

## Como Gerar a Versão Portátil

Para recompilar a versão portátil (`dist/AllDown-Portable`):

```powershell
.venv\Scripts\python.exe build_portable.py
```

---

## Login no YouTube (Anti-Bot)

Caso o YouTube apresente a mensagem solicitando confirmação de que você não é um robô:
1. Abra o aplicativo.
2. Clique no botão `🔑 Fazer Login no YouTube`.
3. Conclua o login na janela oficial do Google.
4. O aplicativo salvará a sessão em `cookies.txt` e habilitará os downloads protegidos.

---

## Licença

Este projeto é disponibilizado para fins educacionais e de uso pessoal. Observe sempre os termos de serviço das plataformas e os direitos autorais dos conteúdos acessados.
