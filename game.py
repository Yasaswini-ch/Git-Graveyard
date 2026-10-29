import array, json, math, os, random, sys
from datetime import date
import pygame

W, H, SCALE = 320, 180, 4
COLS, SPACING_X, SPACING_Y, MARGIN = 8, 36, 40, 24

NIGHT = (20, 18, 31)
GROUND = (26, 38, 34)
STONE = (138, 138, 155)
GHOST_C = (232, 240, 255)
EPITAPH_C = (200, 200, 120)
NOTE_C = (150, 150, 175)
COL = {
    "#": STONE, "m": (79, 122, 82), "g": GHOST_C, "k": (70, 70, 95),
    "s": (214, 170, 120), "b": (90, 60, 40),
}

SHAPES = {
    "round": [
        "...######...",
        "..########..",
        ".##########.",
        ".##########.",
        ".##########.",
        ".##########.",
        ".##########.",
        ".##########.",
        ".##########.",
        "mm########mm",
    ],
    "cross": [
        ".....##.....",
        ".....##.....",
        "..########..",
        "..########..",
        ".....##.....",
        ".....##.....",
        ".....##.....",
        ".....##.....",
        "....####....",
        "mm.######.mm",
    ],
    "slab": [
        "............",
        "............",
        "............",
        ".##########.",
        "############",
        "############",
        "############",
        "############",
        "############",
        "mm########mm",
    ],
    "obelisk": [
        ".....##.....",
        "....####....",
        "....####....",
        "....####....",
        "....####....",
        "...######...",
        "...######...",
        "..########..",
        "..########..",
        "mm########mm",
    ],
}
KIND = {
    ".py": "cross",
    ".css": "slab", ".scss": "slab", ".html": "slab", ".md": "slab", ".txt": "slab",
    ".jpg": "obelisk", ".jpeg": "obelisk", ".png": "obelisk", ".gif": "obelisk",
    ".svg": "obelisk", ".webp": "obelisk",
}
PLAYER = [
    "..bb..",
    ".bbbb.",
    ".ssss.",
    "..ss..",
    ".mmmm.",
    "mmmmmm",
    ".mmmm.",
    ".m..m.",
    ".k..k.",
]
GHOST = [
    "..ggg..",
    ".ggggg.",
    "ggkgkgg",
    "ggggggg",
    "ggggggg",
    "ggggggg",
    "gg.g.gg",
]

OLDEST_FLAME = ((255, 220, 120), (255, 150, 60))
NEWEST_FLAME = ((150, 200, 255), (90, 150, 255))
ELDER_FLAME = ((255, 200, 110), (230, 130, 50))

def make(rows):
    s = pygame.Surface((len(rows[0]), len(rows)), pygame.SRCALPHA)
    for j, row in enumerate(rows):
        for i, c in enumerate(row):
            if c in COL:
                s.set_at((i, j), COL[c])
    return s

def wrap(text, font, width):
    lines, cur = [], ""
    for w in text.split():
        t = (cur + " " + w).strip()
        if font.size(t)[0] <= width:
            cur = t
        else:
            lines.append(cur)
            cur = w
    lines.append(cur)
    return lines

def lifespan(born, died):
    try:
        return (date.fromisoformat(died) - date.fromisoformat(born)).days
    except ValueError:
        return None

def make_step():
    if not pygame.mixer.get_init():
        return None
    _, _, channels = pygame.mixer.get_init()
    rng = random.Random(3)
    n = 1300
    buf, lp = array.array("h"), 0.0
    for i in range(n):
        lp += (rng.uniform(-1, 1) - lp) * 0.25
        buf.extend([int(lp * 9000 * (1 - i / n) ** 2)] * channels)
    s = pygame.mixer.Sound(buffer=buf.tobytes())
    s.set_volume(0.5)
    return s

def immortal(screen, canvas, clock, font, player, ghost):
    rng = random.Random(1)
    stars = [(rng.randrange(W), rng.randrange(H)) for _ in range(40)]
    lines = ["THIS REPO IS IMMORTAL", "No file was ever deleted.", "The gravedigger has nothing to do."]
    lh = font.get_linesize() + 4
    t = 0.0
    while True:
        t += clock.tick(60) / 1000
        for e in pygame.event.get():
            if e.type == pygame.QUIT or (e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE):
                return
            if e.type == pygame.KEYDOWN and e.key == pygame.K_F12:
                pygame.image.save(screen, "shot.png")
        canvas.fill(GROUND)
        for sx, sy in stars:
            canvas.set_at((sx, sy), GHOST_C)
        bob = int(math.sin(t * 2) * 3)
        pygame.draw.ellipse(canvas, GHOST_C, (W // 2 - 10, 38 + bob, 20, 6), 1)
        canvas.blit(ghost, (W // 2 - 3, 46 + bob))
        canvas.blit(player, (W // 2 - 3, 110))
        pygame.transform.scale(canvas, screen.get_size(), screen)
        for n, line in enumerate(lines):
            surf = font.render(line, False, GHOST_C if n == 0 else EPITAPH_C)
            screen.blit(surf, ((screen.get_width() - surf.get_width()) // 2, 270 + n * lh))
        pygame.display.flip()

def main():
    paths = sys.argv[1:3] or ["graves.json"]
    sets = []
    for p in paths:
        try:
            with open(p, encoding="utf-8") as f:
                sets.append(json.load(f))
        except FileNotFoundError:
            sys.exit(f"{p} not found. Run graveyard.py on a repo with deleted files.")
    graves = sets[0]
    # the second file (if any) is the same repo run through another model, matched by path + death date
    by_key = [{(g["path"], g["died"]): g for g in s} for s in sets]
    cur = 0

    def view(i):
        g = graves[i]
        return by_key[cur].get((g["path"], g["died"]), g)

    pygame.mixer.pre_init(22050, -16, 1, 512)
    pygame.init()
    screen = pygame.display.set_mode((W * SCALE, H * SCALE))
    pygame.display.set_caption("Git Graveyard")
    canvas = pygame.Surface((W, H))
    clock = pygame.time.Clock()

    # Text is drawn at screen resolution (not on the 320x180 canvas) so it stays legible.
    if os.path.exists("PressStart2P.ttf"):
        font = pygame.font.Font("PressStart2P.ttf", 16)
    else:
        font = pygame.font.SysFont("consolas,dejavusansmono,couriernew", 20)
    lh = font.get_linesize() + 4

    tombs = {k: make(v) for k, v in SHAPES.items()}
    player, ghost = make(PLAYER), make(GHOST)
    ghost2 = ghost.copy()
    ghost.set_alpha(150)
    ghost2.set_alpha(100)

    if not graves:
        immortal(screen, canvas, clock, font, player, ghost)
        return

    step = make_step()
    step_t = 0.0

    rows = (len(graves) + COLS - 1) // COLS
    world_w = MARGIN * 2 + COLS * SPACING_X
    world_h = MARGIN * 2 + rows * SPACING_Y
    pos = [world_w / 2, 12.0]
    g2 = [world_w * 0.75, 70.0]

    rng = random.Random(1)
    stars = [(rng.randrange(world_w), rng.randrange(world_h)) for _ in range(60)]
    sprites = [tombs[KIND.get(os.path.splitext(g["path"])[1].lower(), "round")] for g in graves]
    ages = [lifespan(g["born"], g["died"]) for g in graves]
    # git log lists newest deaths first, so ties go to the last index for oldest and the first for newest
    oldest = min(range(len(graves)), key=lambda i: (graves[i]["born"], -i))
    newest = max(range(len(graves)), key=lambda i: (graves[i]["died"], -i))
    oldest_name = os.path.basename(graves[oldest]["path"])

    def grave_xy(i):
        return MARGIN + (i % COLS) * SPACING_X, MARGIN + 6 + (i // COLS) * SPACING_Y

    def candle(i):
        # (flame colours, note shown in the grave box)
        if i == oldest:
            return OLDEST_FLAME, "candle: oldest grave in the yard"
        if i == newest:
            return NEWEST_FLAME, "blue flame: freshest grave"
        if ages[i] is not None and ages[i] >= 365:
            return ELDER_FLAME, "candle: lived over a year"
        return None, None

    reading = None
    t = 0.0
    while True:
        dt = clock.tick(60) / 1000
        t += dt

        near = None
        best = 18
        px, py = pos[0] + 3, pos[1] + 5
        for i in range(len(graves)):
            gx, gy = grave_xy(i)
            d = math.hypot(px - (gx + 6), py - (gy + 5))
            if d < best:
                best, near = d, i

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                return
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    return
                if e.key == pygame.K_e:
                    reading = near if reading is None else None
                if e.key == pygame.K_TAB and len(sets) > 1:
                    cur = 1 - cur
                if e.key == pygame.K_F12:
                    pygame.image.save(screen, "shot.png")
        if reading is not None and reading != near:
            reading = None

        keys = pygame.key.get_pressed()
        dx = (keys[pygame.K_RIGHT] or keys[pygame.K_d]) - (keys[pygame.K_LEFT] or keys[pygame.K_a])
        dy = (keys[pygame.K_DOWN] or keys[pygame.K_s]) - (keys[pygame.K_UP] or keys[pygame.K_w])
        pos[0] = max(0, min(world_w - 6, pos[0] + dx * 60 * dt))
        pos[1] = max(0, min(world_h - 9, pos[1] + dy * 60 * dt))

        step_t = step_t - dt if (dx or dy) else 0.0
        if (dx or dy) and step_t <= 0 and step:
            step.play()
            step_t = 0.28

        # the second ghost wanders left, but drifts over to the gravedigger at a grave
        k = min(1.0, dt * 1.5)
        if near is not None:
            g2[0] += (pos[0] + 10 - g2[0]) * k
            g2[1] += (pos[1] - 10 - g2[1]) * k
        else:
            g2[0] = (g2[0] - 15 * dt) % (world_w + 20)
            g2[1] += (70 + math.sin(t * 1.5) * 8 - g2[1]) * min(1.0, dt)

        cam_x = max(0, min(world_w - W, pos[0] - W / 2))
        cam_y = max(0, min(world_h - H, pos[1] - H / 2))
        cx, cy = int(cam_x), int(cam_y)

        canvas.fill(GROUND)
        for sx, sy in stars:
            if 0 <= sx - cx < W and 0 <= sy - cy < H:
                canvas.set_at((sx - cx, sy - cy), GHOST_C)

        for i in range(len(graves)):
            gx, gy = grave_xy(i)
            canvas.blit(sprites[i], (gx - cx, gy - cy))
            flames, _ = candle(i)
            if flames:
                flame = flames[int(t * 4 + i) % 2]
                pygame.draw.rect(canvas, GHOST_C, (gx + 14 - cx, gy + 7 - cy, 2, 3))
                pygame.draw.rect(canvas, flame, (gx + 14 - cx, gy + 5 - cy, 2, 2))

        gxp = (t * 20) % (world_w + 20) - 10
        gyp = 14 + math.sin(t * 2) * 6
        canvas.blit(ghost, (int(gxp) - cx, int(gyp) - cy))
        canvas.blit(ghost2, (int(g2[0]) - cx, int(g2[1] + math.sin(t * 3) * 2) - cy))
        canvas.blit(player, (int(pos[0]) - cx, int(pos[1]) - cy))

        overlay = []  # (surface, screen_x, screen_y)

        def put(text, color, x, y, right=False):
            surf = font.render(text, False, color)
            overlay.append((surf, screen.get_width() - surf.get_width() - 12 if right else x, y))

        if near is not None and reading is None:
            put("E: read", GHOST_C, 12, 10)
        put(f"{len(graves)} buried | oldest: {oldest_name}", NOTE_C, 0, 10, right=True)
        if len(sets) > 1:
            put(f"model: {view(0).get('model', '?')}  [Tab] switch", NOTE_C, 0, 10 + lh, right=True)

        if reading is not None:
            g = view(reading)
            n_days = ages[reading]
            span = f" ({n_days} day{'s' if n_days != 1 else ''})" if n_days is not None else ""
            lines = [(os.path.basename(g["path"]), GHOST_C),
                     (f"{g['born']} - {g['died']}{span}", GHOST_C),
                     ("killed by " + g["killer"], GHOST_C)]
            lines += [(l, EPITAPH_C) for l in wrap(g["epitaph"], font, (W - 12) * SCALE - 24)]
            if g.get("model"):
                lines.append(("model: " + g["model"], NOTE_C))
            note = candle(reading)[1]
            if note:
                lines.append((note, NOTE_C))
            box_h = (len(lines) * lh + 16) // SCALE + 1
            box = pygame.Rect(6, H - box_h - 6, W - 12, box_h)
            pygame.draw.rect(canvas, NIGHT, box)
            pygame.draw.rect(canvas, STONE, box, 1)
            for n, (line, color) in enumerate(lines):
                put(line, color, box.x * SCALE + 12, box.y * SCALE + 8 + n * lh)

        pygame.transform.scale(canvas, screen.get_size(), screen)
        for surf, x, y in overlay:
            screen.blit(surf, (x, y))
        pygame.display.flip()

main()
