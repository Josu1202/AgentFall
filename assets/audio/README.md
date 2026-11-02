# Sustitucion de sonidos

No hacen falta archivos de audio: `audio.py` sintetiza todos los efectos.
Para sustituirlos, coloca aqui un archivo WAV u OGG con uno de estos nombres:

`shoot`, `hit`, `death`, `pickup`, `level_up`, `damage`, `ability`,
`game_over`, `victory`, `select`.

Ejemplo: `pickup.wav` reemplaza el tono de recogida. Se prefiere WAV sobre OGG
si existen ambos. Si un archivo no puede cargarse, se usa el sonido sintetizado.
Los recursos deben tener una licencia compatible con el uso que quieras darles.
