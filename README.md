# Zoom Automatic

Ferramenta desktop para Linux que automatiza cortes dinâmicos de câmera (*punch-in* e *smooth zoom*) baseados nas pausas da fala e mantém o apresentador enquadrado automaticamente por meio de detecção facial.

Ideal para agilizar a pré-edição de vídeos falados, o **Zoom Automatic** processa o arquivo original, preserva a faixa de áudio sem recompressão e exporta um novo `.mp4` pronto para ser importado na timeline de qualquer editor de vídeo (incluindo editores executados em ambientes isolados, como Flatpak ou AppImage).

---

## Funcionalidades

* **Detecção automática de pausas:** Analisa a faixa de áudio via FFmpeg (`silencedetect`) para identificar intervalos naturais entre frases e posicionar os cortes de zoom.
* **Enquadramento facial (Face Lock):** Localiza o maior rosto em quadro com OpenCV (`Haar Cascade`) e ajusta o ponto de ancoragem do recorte para manter o apresentador centralizado.
* **Dois modos de movimento:**
  * `punch`: corte seco instantâneo entre o plano aberto (`1.0x`) e o plano aproximado.
  * `smooth`: aproximação e recuo progressivos com curva suave (*ease-in-out*).
* **Parâmetros ajustáveis:** Controle da intensidade do zoom (`1.10x` a `1.60x`), intervalo mínimo entre cortes (em segundos) e ativação/desativação do rastreamento facial.
* **Exportação compatível:** Renderiza o vídeo em H.264 (`libx264`, `yuv420p`, CRF 18) com correção automática de dimensões pares e cópia direta do áudio original (`-c:a copy`).

---

## Dependências

### 1. Para usar o Executável (`Zoom-Automatic`)
O executável já embute o interpretador Python, a interface gráfica e o OpenCV. A única dependência externa necessária no sistema é o **FFmpeg**:

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

### 2. Para rodar ou compilar pelo Código-Fonte
Além do **FFmpeg**, são necessários os pacotes base do Python para ambientes virtuais e interface gráfica (**Tkinter**), junto com as bibliotecas listadas abaixo:

* **Dependências de sistema (Ubuntu/Debian/Mint):**
  ```bash
  sudo apt update && sudo apt install -y ffmpeg python3 python3-venv python3-tk
  ```
* **Dependências Python (`requirements.txt`):**
  * `opencv-python-headless` — processamento de frames, recorte e detecção facial sem conflito gráfico com o Tkinter.
  * `pyinstaller` *(opcional)* — necessário apenas para empacotar o código em um executável único.

---

## Como usar o Executável (Linux)

1. Acesse a aba **[Releases](../../releases)** deste repositório e baixe o arquivo `Zoom-Automatic`.
2. Abra o terminal na pasta onde salvou o arquivo e dê permissão de execução:
   ```bash
   chmod +x Zoom-Automatic
   ```
3. Inicie o programa com duplo clique ou pelo terminal:
   ```bash
   ./Zoom-Automatic
   ```
4. Escolha o estilo de zoom, a intensidade e o intervalo mínimo entre cortes.
5. Clique em **Selecionar Vídeo e Gerar Zoom** e escolha o arquivo desejado (`.mp4`, `.mov`, `.mkv`, `.avi` ou `.webm`).
6. Ao concluir, um arquivo `nome_do_video_zoom.mp4` será salvo na mesma pasta do original, pronto para ser arrastado para o seu editor de vídeo.

---

## Instalação e execução pelo Código-Fonte

1. Clone o repositório e entre na pasta do projeto:
   ```bash
   git clone [https://github.com/SEU_USUARIO/zoom-automatic.git](https://github.com/SEU_USUARIO/zoom-automatic.git)
   cd zoom-automatic
   ```

2. Crie um ambiente virtual isolado (`.venv`) e instale as dependências:
   ```bash
   python3 -m venv .venv
   .venv/bin/python -m ensurepip --upgrade
   .venv/bin/python -m pip install --upgrade pip
   .venv/bin/python -m pip install -r requirements.txt
   ```

3. Execute a aplicação (a variável `PYTHONNOUSERSITE=1` evita conflitos com pacotes globais do sistema):
   ```bash
   PYTHONNOUSERSITE=1 .venv/bin/python main.py
   ```

---

## Como gerar o Executável Único (Build)

Com o ambiente virtual `.venv` configurado, instale o PyInstaller e compile o projeto em um único binário independente:

```bash
PYTHONNOUSERSITE=1 .venv/bin/python -m pip install pyinstaller

PYTHONNOUSERSITE=1 .venv/bin/pyinstaller \
  --onefile \
  --noconsole \
  --name "Zoom-Automatic" \
  --collect-data cv2 \
  main.py
```

O executável pronto será gerado em `dist/Zoom-Automatic`.

### Adicionar atalho no menu de aplicativos do Linux (opcional)

```bash
cat << 'EOF' > ~/.local/share/applications/zoom-automatic.desktop
[Desktop Entry]
Name=Zoom Automatic
Comment=Aplica zoom dinâmico e rastreamento facial em vídeos
Exec="/CAMINHO/COMPLETO/PARA/Zoom-Automatic"
Icon=video-x-generic
Terminal=false
Type=Application
Categories=AudioVideo;Video;
EOF
```
*(Substitua `/CAMINHO/COMPLETO/PARA/Zoom-Automatic` pelo local onde o executável está salvo.)*

---

## Estrutura do Projeto

```text
zoom-automatic/
├── main.py            # Interface gráfica (Tkinter), barra de progresso e fluxo principal
├── analyzer.py        # Detecção de pausas na fala (FFmpeg) e centro do rosto (OpenCV)
├── zoom_engine.py     # Geração cronológica dos keyframes de escala e ancoragem
├── renderer.py        # Interpolação frame a frame e muxing final de vídeo e áudio
├── requirements.txt   # Dependências Python do projeto
├── .gitignore         # Regras para ignorar .venv, builds e vídeos locais no Git
└── LICENSE            # Licença MIT
```

---

## Licença

Este projeto está sob a licença **MIT**. Veja o arquivo `LICENSE` para mais detalhes.
