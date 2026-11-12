# All Down — YouTube 4K/8K Downloader

[![Download All Down Portable](https://img.shields.io/badge/Download-All%20Down%20Port%C3%A1til-E50914?style=for-the-badge&logo=windows&logoColor=white)](https://github.com/acrisiodejesus/all-down/releases/latest/download/AllDown-Portable.zip)
[![GitHub Releases](https://img.shields.io/badge/Todas%20as%20Vers%C3%B5es-Releases-24292e?style=for-the-badge&logo=github)](https://github.com/acrisiodejesus/all-down/releases)

### 📦 Download da Versão Portátil (Pronta para Usar)

> ⬇️ **[Baixar AllDown-Portable.zip (Versão mais recente)](https://github.com/acrisiodejesus/all-down/releases/latest/download/AllDown-Portable.zip)**
> 
> - **Nenhuma instalação necessária**: não precisa instalar Python, Node.js ou FFmpeg.
> - **Tudo incluso**: FFmpeg, gerador de PO Token e interface gráfica já vêm embutidos.
> - Basta baixar o arquivo `.zip`, extrair em qualquer pasta e dar um duplo clique em **`AllDown.exe`**.

---

All Down é uma aplicação desktop moderna para Windows desenvolvida para realizar downloads de vídeos e áudios do YouTube na resolução máxima disponível (1080p, 2K, 4K Ultra HD e até 8K), contornando as restrições recentes de PO Token (Proof of Origin), n-sig challenges e rate-limiting do YouTube.

---

## Recursos

- **Resoluções Ultra HD**: Download e detecção automática de resoluções de 360p até 4K (2160p) e 8K (4320p).
- **Interface Moderna Windows 11**: Interface gráfica moderna com CustomTkinter em modo Dark, cantos arredondados e layout em cartões.
- **Prévia do Vídeo**: Exibição da thumbnail original, título, canal, duração e badge indicativo de 4K Ultra HD.
- **Muxing via FFmpeg**: Mesclagem de streams separados de vídeo de alta resolução e áudio em contêineres MP4 ou MKV.
- **Autenticação Anti-Robô Integrada**: Janela de login nativa do Google/YouTube via WebView2 (Edge Chromium) para exportação segura de sessão (`cookies.txt`), sem necessidade de instalar extensões no navegador.
- **Bypass de PO Token (bgutil)**: Integração com gerador dinâmico de GVS PO Tokens em segundo plano via Node.js runtime.
- **Distribuição Portátil**: Executável standalone que pode ser executado em qualquer máquina Windows sem necessidade de instalar Python, Node.js ou FFmpeg.

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
