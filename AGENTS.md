# Guia de trabajo para agentes

Este proyecto es una aplicacion de escritorio en CPython 3.12 / 3.13 y pygame 2.6.1.
Lee `README.md` y los modulos que vayas a cambiar antes de editar.

## Arquitectura

- `config.py` es la fuente de valores de equilibrio y contenido compartido.
- `main.py` configura SDL y el mixer antes de crear `Game`.
- `Game` posee el estado de la partida; las entidades guardan coordenadas del mundo.
- `weapons.py` y `upgrades.py` consumen las definiciones de configuracion.
- `Sprites` cachea el arte generado y `Audio.load_sound` permite sustituir sonidos.
- `UI` dibuja sobre un lienzo de 640 x 360. Convierte el raton mediante `canvas_mouse`.
- `.github/workflows/tests.yml` ejecuta pruebas en Windows y Linux, con Python 3.12 / 3.13.
- `run_windows.bat` crea o reutiliza `.venv313` con Python 3.13 de 64 bits.

## Reglas al modificar

1. Conserva `python main.py` como punto de entrada, sin descargas de recursos.
2. Usa segundos y delta time; evita temporizadores basados en numero de fotogramas.
3. Mantiene la simulacion congelada en `upgrade`, `paused` y `game_over`.
4. No pierdas experiencia sobrante ni ofrezcas cartas duplicadas o invalidas.
5. Aplica dano por `Game.damage_enemy`: centraliza muerte, botin y efectos.
6. Respeta los limites de entidades y usa `SpatialHash` en colisiones locales.
7. Mantiene separados el RNG de jugabilidad y el RNG cosmetico.
8. Usa la paleta `P`, pixeles enteros y escalado sin suavizado.
9. Conserva los controles de teclado y raton y la ejecucion sin audio disponible.
10. Comenta decisiones no evidentes; evita dependencias adicionales sin necesidad.

## Validacion

Desde la raiz del proyecto:

```bash
python -m unittest discover -s tests -v
python main.py --smoke-test
```

Si cambias interfaz, comprueba seleccion de los tres agentes, HUD, cartas largas,
pausa y resultados a resolucion interna y a escala 2. Para balance o rendimiento,
simula partidas largas y hordas cercanas al limite; no afirmes 60 FPS universales.
No incluyas `__pycache__`, entornos virtuales ni resultados temporales en el ZIP.
Conserva `.gitignore`, `.gitattributes`, `.editorconfig`, `.python-version` y `.github/`
al empaquetar el proyecto. Consulta `docs/GITHUB.md` para su publicacion.
