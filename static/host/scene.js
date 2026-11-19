import { Application, Container } from "./pixi.js";
import { BoxLayer } from "./box-layer.js";
import { Camera } from "./camera.js";
import { FxLayer } from "./fx-layer.js";
import { MarbleLayer } from "./marble-layer.js";
import { MoverLayer } from "./mover-layer.js";
import { drawTrack } from "./track-view.js";

const BACKGROUND = 0x231f5c;

export class Scene {
  #time = 0;

  constructor(layers, camera) {
    Object.assign(this, layers);
    this.camera = camera;
  }

  static async create(mount, init) {
    const app = await Scene.#startApp(mount);
    const { config, track } = init;
    const layers = {
      boxes: new BoxLayer(track.boxes, config.box_radius),
      movers: new MoverLayer(track.movers),
      marbles: new MarbleLayer(config.radius),
      fx: new FxLayer(config.shock_radius),
    };
    const world = new Container();
    world.addChild(drawTrack(track, config), layers.boxes, layers.movers, layers.marbles, layers.fx);
    app.stage.addChild(world);

    const scene = new Scene(layers, new Camera(world, app.screen, config));
    app.ticker.add((ticker) => scene.update(ticker.deltaMS / 1000));
    return scene;
  }

  static async #startApp(mount) {
    const app = new Application();
    await app.init({
      resizeTo: window,
      background: BACKGROUND,
      antialias: true,
      autoDensity: true,
      resolution: window.devicePixelRatio || 1,
    });
    mount.appendChild(app.canvas);
    return app;
  }

  update(dt) {
    this.#time += dt;
    this.marbles.update();
    this.boxes.update(this.#time);
    this.fx.update(dt);
    this.camera.follow(this.marbles.leaderY());
  }
}