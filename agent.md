# Agentfall: mapa para agentes

La guia de mantenimiento completa esta en [AGENTS.md](AGENTS.md).
Las instrucciones de instalacion y controles estan en [README.md](README.md).

## Donde empezar

- Cambiar personajes, estadisticas, pesos o tiempos: `config.py`.
- Crear una habilidad activa: `Game.activate_ability` en `game.py`.
- Cambiar decisiones del autopiloto: `Game.auto_direction` en `game.py`.
- Agregar un ataque: definicion en `config.py` y comportamiento en `weapons.py`.
- Agregar enemigos: `config.py`, `enemies.py` y el dibujo en `sprites.py`.
- Agregar mejoras: `config.py` y `upgrades.py`.
- Sustituir efectos de sonido: `assets/audio/` o `Audio.load_sound`.

Los agentes seleccionables son Planner, Retriever y Generator; sus habilidades y
pasivas pertenecen a la partida. El autopiloto es opcional y el teclado lo anula
mientras se pulsa una direccion.
