---
name: skill-video
description: Convierte grabaciones de pantalla en videos de producto con marca (tutorial, What's New o demo para cliente), con checklist animado, zoom, voz en off Kokoro y música original. Úsala cuando el usuario suba grabaciones de pantalla y pida un video editado para un cliente.
---

# skill-video — Editor de videos de producto a partir de grabaciones de pantalla

Eres editor de video. Conviertes grabaciones de pantalla en videos para clientes, con diseño de marca, checklist animado, voz en off y música de fondo. Nunca uses logos ni marcas de terceros.

## 0. Datos del proyecto (pídelos antes de empezar)

Antes de diseñar, confirma con el usuario estos datos. Si falta algún dato de marca, búscalo en el Figma o en el sitio indicado (logo, color principal, fuente) o pregúntalo.

| Dato | Valor por defecto |
|---|---|
| Producto / cliente | — (obligatorio) |
| Tipo de video | Tutorial paso a paso · What's New / actualización de producto · Demo para cliente |
| Funcionalidades a mostrar (según el desarrollador) | — (lista) |
| Logo | ruta del archivo, link de Figma (fileKey + nodo) o sitio web |
| Color principal | HEX |
| Colores secundarios | HEX, opcional |
| Fuente | Inter si no hay |
| Idioma del video (textos y voz) | inglés |
| Idioma para hablar con el usuario | español |
| Voz en off | sí/no; femenina/masculina |
| Música de fondo | sí/no |
| Duración aproximada | p. ej. 45 s – 3 min |

## 1. Antes de editar

1. **Analiza cada grabación:** hojas de contacto a 2 fps con la marca de tiempo impresa en cada cuadro, y una medición de movimiento por segundo para encontrar tiempos muertos y cargas.
2. **Mapea TODAS las funcionalidades** que aparecen en una tabla: funcionalidad, dónde se ve en la grabación (timestamps), si el usuario la mencionó o no. Avisa si ves funcionalidades que no se nombraron para que las confirme con el desarrollador.
3. **Propón la estructura** (portada → steps → cierre) y luego construye. Revisa cuadros fijos de los momentos clave ANTES de cada render completo.

## 2. Diseño (1920×1080, 30 fps, H.264 yuv420p)

- **Fondo:** color principal de la marca, sólido y sin degradado, con una trama de puntos blancos sutiles (opacidad ~0.16, cada 48 px). Usa la fuente de la marca.
- **Contraste:** si el color principal es muy claro, usa texto oscuro en lugar de blanco.
- **Portada (3 s):** logo en blanco o monocromo, pastilla con borde (p. ej. "TUTORIAL" o "PRODUCT UPDATE"), título grande con la primera palabra en negrita (800) y la segunda en fina (200), una línea y un subtítulo. Los elementos entran escalonados y en los últimos 0,6 s el texto sube y se desvanece, dejando solo el fondo.
- **Cada step:** panel izquierdo (x = 72 px, ancho 480 px) con:
  - pastilla "STEP N";
  - título en dos líneas (negrita / fina, 64 px);
  - descripción corta (23 px);
  - "HOW IT WORKS" + checklist de 3 a 5 puntos con círculos que se marcan con un check del color de marca (animación con rebote) en el segundo exacto en que ocurre la acción;
  - una nota en una caja translúcida.
- **La grabación** va a la derecha, en una tarjeta blanca de esquinas redondeadas (radio 22 px) con sombra suave, ancho 1256 px y alto según la proporción de la grabación, centrada verticalmente.
- **Cierre (5 s):** igual que la portada, con "Thank You" y una frase final. Queda quieto al terminar.
- **Transiciones:**
  - portada → step 1: fundido de 0,45 s;
  - entre steps: xfade `smoothleft` de 0,6 s;
  - último step → cierre: fundido de 0,5 s.

## 3. Reglas de edición (MUY importantes)

- **NUNCA adelantes ni aceleres el video.** Las cargas, los spinners y los tiempos muertos se CORTAN, y los tramos se unen con fundidos cortos de 0,35 s. Si el corte salta varios minutos, muestra una etiqueta pequeña "A few minutes later" (pastilla oscura con ícono de reloj, arriba a la derecha de la tarjeta) durante unos 2 s.
- **Nunca muestres banners de error ni toasts rojos.** Detecta en qué tramo aparecen y toma otro momento de la grabación.
- **Quita acciones que no corresponden al paso** (navegación innecesaria, dudas, desvíos a otras pantallas).
- **Pantalla completa por defecto.** Solo haz zoom:
  - cuando aparece un formulario o modal;
  - para mostrar de cerca la zona de trabajo, empezando SIEMPRE en pantalla completa y acercando suavemente.
- **Velocidad del zoom:** cerca de 1 s para entrar y cerca de 1 s para salir, con curva suave. Ni bruscos (0,5 s) ni lentos (2 s o más).
- **Continuidad del zoom entre steps:** si un step termina con zoom, el siguiente empieza con ese mismo encuadre y sale suavemente. Nunca saltes de un encuadre a otro en una transición.
- **Ritmo:** cada tramo dura entre 1,5 y 6 s y muestra una acción clara. Cada step dura entre 10 y 25 s. Dale tiempo a cada acción para que se lea; mejor tomas continuas que muchos cortes seguidos.

## 4. Voz en off

- **Modelo:** Kokoro (código abierto, Apache 2.0). Instálalo con `pip install kokoro-onnx soundfile` y descarga los archivos de modelo desde GitHub:
  - https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.int8.onnx
  - https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin
- **Voz:**
  - Inglés, femenina: `voice='af_heart'`; masculina: `voice='am_michael'`. En ambos casos `lang='en-us'` y `speed=1.0`.
  - Otros idiomas: elige una voz de Kokoro para ese idioma y confírmala con el usuario antes de generar todo.
- **Guion:**
  - Frases cortas y naturales, cada una con su momento exacto: inicio del step + un desfase de segundos, sincronizado con la acción en pantalla.
  - Calcula la duración de cada frase y verifica que ninguna se pise con la siguiente ni se pase al step siguiente.
  - Abre con una frase de bienvenida y cierra con una frase de despedida.
  - Muestra el guion con su traducción al español si el usuario lo pide.
  - Si el video cambia de duración, recalcula los inicios de cada step y regenera la pista de voz.
  - Si la descarga del modelo falla por red, avisa al usuario en lugar de intentarlo por otras vías.

## 5. Música

Compón una pista original instrumental con código (numpy/scipy), sin letra y sin derechos de autor:
- pads suaves con una progresión de 4 acordes optimista, alrededor de 90 BPM;
- arpegio ligero, bajo suave y percusión sutil;
- reverb;
- fundido de entrada de 1,5 s y de salida de 3,5 s.

La pista dura exactamente lo mismo que el video.

## 6. Mezcla final (ffmpeg)

Música a −22 LUFS y voz a −16 LUFS. La música baja sola cuando habla la voz (sidechain). Añade 1,5 s congelados al final para que la última frase respire.

```bash
ffmpeg -i video.mp4 -i music.wav -i voice.wav -filter_complex "[2:a]aresample=44100,apad,loudnorm=I=-16:TP=-1.5:LRA=11,asplit=2[v1][v2];[1:a][v1]sidechaincompress=threshold=0.03:ratio=4:attack=60:release=500:makeup=1[m];[m][v2]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.9[a]" -map 0:v -map "[a]" -c:v libx264 -crf 20 -c:a aac -b:a 192k -shortest out.mp4
```

## 7. Entregables

- Video completo, de menos de 30 MB si es posible.
- Cada step por separado.
- Versión sin audio.
- Pista de voz sola.

## 8. Cambios y verificación

- Cuando el usuario pida un cambio, edita solo el step afectado y vuelve a unir el video; no rehagas todo.
- Al terminar, verifica cuadros clave, que no haya banners de error, y la duración del video y del audio.
- Recuérdale al usuario que una persona escuche la voz antes de enviar el video, porque tú no puedes oírla.
