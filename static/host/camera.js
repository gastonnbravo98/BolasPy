const DESIGN_HEIGHT = 900;

export class Camera {
  #y = 0;

  constructor(world, screen, config) {
    this.world = world;
    this.screen = screen;
    this.config = config;
  }

  follow(leaderY) {
    const scale = this.#scale();
    this.#y += (this.#targetY(leaderY, scale) - this.#y) * 0.08;
    this.world.scale.set(scale);
    this.world.x = (this.screen.width - this.config.world_w * scale) / 2;
    this.world.y = -this.#y;
  }

  #scale() {
    return Math.min(this.screen.width / this.config.world_w, this.screen.height / DESIGN_HEIGHT);
  }

  #targetY(leaderY, scale) {
    const max = Math.max(0, this.config.world_h * scale - this.screen.height);
    const wanted = leaderY * scale - this.screen.height * 0.4;
    return Math.min(max, Math.max(0, wanted));
  }
}
