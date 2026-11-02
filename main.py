"""Entry point. Run `python main.py`; no downloaded assets are needed."""
import argparse
import os


def main() -> None:
    parser = argparse.ArgumentParser(description="AGENTFALL - pygame survival roguelite")
    parser.add_argument("--mute", action="store_true", help="Start with sound muted")
    parser.add_argument("--seed", type=int, help="Reproducible run seed")
    parser.add_argument("--smoke-test", action="store_true", help="Run 180 headless frames and exit")
    args = parser.parse_args()
    if args.smoke_test:
        os.environ["SDL_VIDEODRIVER"] = "dummy"
        os.environ["SDL_AUDIODRIVER"] = "dummy"
    os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
    try:
        import pygame
    except ImportError as exc:
        raise SystemExit("Falta pygame. Ejecuta: python -m pip install -r requirements.txt") from exc
    from config import AUDIO
    from game import Game

    pygame.mixer.pre_init(AUDIO["rate"], -16, 1, 512)
    pygame.init()
    try:
        game = Game(seed=args.seed, muted=args.mute)
        if args.smoke_test:
            game.start_run("planner")
            game.player.autopilot = True
            for _ in range(180):
                game.update(1 / 60)
                game.draw()
            print(f"Smoke test OK: {game.elapsed:.1f}s, {len(game.enemies)} enemies")
        else:
            game.run()
    finally:
        pygame.quit()


if __name__ == "__main__":
    main()
