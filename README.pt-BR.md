[English](README.md) | **Português (Brasil)**

# Zoom Automatic

Utilitário desktop para Linux com interface escura inspirada no macOS que automatiza cortes dinâmicos de câmera (*punch-in* e *smooth zoom*) baseados nas pausas da fala e mantém o apresentador centralizado por meio de detecção facial.

Projetado para agilizar a pré-edição de vídeos falados, o **Zoom Automatic** processa o vídeo bruto, preserva a trilha de áudio original sem recompressão e exporta um `.mp4` pronto para qualquer editor de vídeo (incluindo editores executados via Flatpak ou AppImage).

---

## Funcionalidades

* **Detecção Automática de Pausas:** Analisa a faixa de áudio via FFmpeg (`silencedetect`) para posicionar as transições de zoom nos intervalos naturais entre frases.
* **Face Lock (Enquadramento Facial):** Detecta o rosto principal em quadro com OpenCV (`Haar Cascade`) e ajusta o ponto de ancoragem do recorte para manter o apresentador centralizado.
* **Aba de Pré-visualização Rápida (30s):** Cria um cache proxy leve na memória RAM com os primeiros 30 segundos para reprodução fluida, navegação interativa na linha do tempo, salto entre cortes e guia visual da área de recorte.
* **Dois Estilos de Movimento:**
  * **Corte Seco (`punch`):** Transição instantânea entre o plano aberto (`1.0x`) e o plano aproximado.
  * **Suave (`smooth`):** Aproximação e recuo progressivos com curva *ease-in-out*.
* **Exportação Flexível:** Permite exportar o **vídeo completo** ou apenas o **trecho de 30 segundos** em H.264 (`libx264`, `yuv420p`, CRF 18) com cópia direta do áudio original (`-c:a copy`).

---

## Dependências

### 1. Executável Único para Linux (`Zoom-Automatic`)
O binário compilado já embute o Python, o Tkinter e o OpenCV. Apenas o **FFmpeg** precisa estar instalado no sistema:

* **Ubuntu / Debian / Linux Mint:**
  ```bash
  sudo apt update && sudo apt install -y ffmpeg
  ```
* **Fedora:**
  ```bash
  sudo dnf install -y ffmpeg
  ```
* **Arch Linux:**
  ```bash
  sudo pacman -S ffmpeg
  ```

### 2. Rodar ou Compilar pelo Código-Fonte
Além do **FFmpeg**, a execução pelo código-fonte exige os pacotes de ambiente virtual e interface gráfica do Python:

* **Pacotes do sistema (Ubuntu / Debian / Mint):**
  ```bash
  sudo apt update && sudo apt install -y ffmpeg python3 python3-venv python3-tk
  ```
* **Dependências Python (`requirements.txt`):**
  * `opencv-python-headless` — processamento de frames, recorte e detecção facial sem conflito com o Tkinter.
  * `pyinstaller` *(opcional)* — necessário apenas para empacotar o projeto em um executável único.

---

## Como Usar (Executável Linux)

1. Baixe o arquivo **`Zoom-Automatic`** na aba **[Releases](../../releases)**.
2. Dê permissão de execução ao binário:
   ```bash
   chmod +x Zoom-Automatic
   ```
3. Inicie com duplo clique ou pelo terminal:
   ```bash
   ./Zoom-Automatic
   ```
4. Escolha o **Vídeo Original** e **Onde Salvar**, ajuste os parâmetros de zoom, confira os cortes na aba **Pré-visualização** e clique em **Exportar Vídeo Completo**.

---

## Instalação pelo Código-Fonte

1. Clone o repositório e entre na pasta do projeto:
   ```bash
   git clone [https://github.com/oudim/zoom-automatic.git](https://github.com/oudim/zoom-automatic.git)
   cd zoom-automatic
   ```

2. Crie um ambiente virtual isolado (`.venv`) e instale as dependências:
   ```bash
   python3 -m venv .venv
   .venv/bin/python -m ensurepip --upgrade
   .venv/bin/python -m pip install --upgrade pip
   .venv/bin/python -m pip install -r requirements.txt
   ```

3. Execute a aplicação:
   ```bash
   PYTHONNOUSERSITE=1 .venv/bin/python main.py
   ```

---

## Como Compilar o Executável Único

Com o `.venv` configurado, instale o PyInstaller e empacote todos os módulos em um único binário para Linux:

```bash
PYTHONNOUSERSITE=1 .venv/bin/python -m pip install pyinstaller

PYTHONNOUSERSITE=1 .venv/bin/pyinstaller \
  --onefile \
  --noconsole \
  --paths . \
  --name "Zoom-Automatic" \
  --collect-data cv2 \
  main.py
```

O executável final será gerado em `dist/Zoom-Automatic`.

---

## Estrutura do Projeto

```text
zoom-automatic/
├── main.py                  # Ponto de entrada da aplicação
├── requirements.txt         # Dependências Python
├── .gitignore               # Arquivos ignorados pelo Git
├── LICENSE                  # Licença MIT
├── core/
│   ├── analyzer.py          # Metadados, detecção de silêncio (FFmpeg) e ancoragem facial
│   ├── zoom_engine.py       # Geração de keyframes, interpolação e geometria de recorte
│   ├── preview_engine.py    # Cache proxy de 30s em RAM e renderização do guia de corte
│   └── renderer.py          # Renderização final/parcial em H.264 e muxing de áudio
└── ui/
    ├── theme.py             # Paleta macOS Dark e widgets customizados em Canvas
    ├── editor_tab.py        # Seletores de origem/destino, ajustes de zoom e exportação
    ├── preview_tab.py       # Player de prévia em tempo real, timeline e navegação de cortes
    └── app_window.py        # Janela principal e barra segmentada de abas
```

---

## Licença

Distribuído sob a licença **MIT**. Consulte o arquivo [LICENSE](LICENSE) para mais detalhes.
