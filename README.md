# Zoom-Automatic

Ferramenta auxiliar para criadores de conteudo no Linux que automatiza cortes dinâmicos de câmera (*punch-in* e *smooth zoom*) baseados nas pausas da fala e mantém o apresentador enquadrado automaticamente por meio de detecção facial.

Projetado especialmente para fluxos em que o editor roda em ambiente isolado (como via **Flatpak**), o AutoZoom processa o vídeo original, preserva a faixa de áudio sem perda e exporta um novo arquivo `.mp4` pronto para ser arrastado diretamente para a timeline.

---

## Funcionalidades

* **Detecção automática de pausas:** Analisa o áudio via FFmpeg (`silencedetect`) para identificar intervalos naturais entre frases e posicionar os cortes de zoom.
* **Face Lock (Rastreamento Facial):** Localiza o maior rosto em quadro com OpenCV (`Haar Cascade`) e ajusta o ponto de ancoragem do recorte para manter o apresentador centralizado.
* **Dois modos de movimento:**
  * `punch`: corte seco instantâneo entre o plano aberto (`1.0x`) e o zoom (estilo Reels, TikTok e YouTube Shorts).
  * `smooth`: aproximação e recuo progressivos com curva suave (*ease-in-out*).
* **Parâmetros ajustáveis:** Controle da intensidade do zoom (`1.10x` a `1.60x`), intervalo mínimo entre cortes (em segundos) e ativação/desativação do *Face Lock*.
* **Exportação compatível:** Renderiza o vídeo em H.264 (`libx264`, `yuv420p`, CRF 18) com correção automática de dimensões pares e cópia direta do áudio original (`-c:a copy`).

---

## Dependências

### 1. Para usar o Executável (`AutoZoom-Filmcraft`)
O executável já embute o Python, a interface gráfica e o OpenCV. A única dependência externa necessária no sistema é o **FFmpeg**:

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
Além do **FFmpeg**, você precisará dos pacotes base do Python para ambientes virtuais e interface gráfica (**Tkinter**), além das bibliotecas Python listadas abaixo:

* **Dependências de sistema (Ubuntu/Debian/Mint):**
  ```bash
  sudo apt update && sudo apt install -y ffmpeg python3 python3-venv python3-tk
  ```
* **Dependências Python (`requirements.txt`):**
  * `opencv-python-headless` — processamento de frames, recorte e detecção facial sem conflito gráfico com o Tkinter.
  * `pyinstaller` *(opcional)* — necessário apenas se você quiser empacotar o código em um executável único.

---

## Como usar o Executável (Linux)

1. Acesse a aba **[Releases](../../releases)** deste repositório e baixe o arquivo `AutoZoom-Filmcraft`.
2. Abra o terminal na pasta onde salvou o arquivo e dê permissão de execução:
   ```bash
   chmod +x AutoZoom-Filmcraft
   ```
3. Inicie o programa com duplo clique ou pelo terminal:
   ```bash
   ./AutoZoom-Filmcraft
   ```
4. Configure o estilo de zoom, a intensidade e o intervalo mínimo.
5. Clique em **Selecionar Vídeo e Gerar AutoZoom** e escolha o arquivo desejado (`.mp4`, `.mov`, `.mkv`, `.avi` ou `.webm`).
6. Ao concluir, um arquivo `nome_do_video_autozoom.mp4` será salvo na mesma pasta do original — basta arrastá-lo para a timeline do **Filmcraft**.

---

## Instalação e execução pelo Código-Fonte

1. Clone o repositório e entre na pasta do projeto:
   ```bash
   git clone [https://github.com/SEU_USUARIO/filmcraft-autozoom.git](https://github.com/SEU_USUARIO/filmcraft-autozoom.git)
   cd filmcraft-autozoom
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
  --name "AutoZoom-Filmcraft" \
  --collect-data cv2 \
  main.py
```

O executável pronto será gerado em `dist/AutoZoom-Filmcraft`.

### Adicionar atalho no menu de aplicativos do Linux (opcional)

```bash
cat << 'EOF' > ~/.local/share/applications/filmcraft-autozoom.desktop
[Desktop Entry]
Name=AutoZoom (Filmcraft)
Comment=Aplica zoom dinâmico e rastreamento facial em vídeos
Exec="/CAMINHO/COMPLETO/PARA/AutoZoom-Filmcraft"
Icon=video-x-generic
Terminal=false
Type=Application
Categories=AudioVideo;Video;
EOF
```
*(Substitua `/CAMINHO/COMPLETO/PARA/AutoZoom-Filmcraft` pelo local onde o executável está salvo.)*

---

## Estrutura do Projeto

```text
filmcraft-autozoom/
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
