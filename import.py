import os
import math
import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GL import shaders

# --------------------------------------------------------------------------------
#   Wave & water with animated cubemap reflection, refraction + radial ripples
# --------------------------------------------------------------------------------


# Vertex shader for water effects (bez zmian)
VERTEX_SHADER = """
#version 120
varying vec3 normal;
varying vec3 position;
varying vec3 incident;

void main() {
    normal = normalize(gl_NormalMatrix * gl_Normal);
    position = vec3(gl_ModelViewMatrix * gl_Vertex);
    incident = normalize(position);
    gl_Position = gl_ModelViewProjectionMatrix * gl_Vertex;
}
"""

# Fragment shader for water effects (bez zmian)
FRAGMENT_SHADER = """
#version 120
varying vec3 normal;
varying vec3 position;
varying vec3 incident;
uniform samplerCube cubemap;
uniform float time;

void main() {
    vec3 N = normalize(normal);
    vec3 I = normalize(incident);
    
    // Fresnel effect
    float ratio = 1.00 / 1.33; // Air to water ratio
    float fresnel = pow(1.0 - dot(-I, N), 4.0);
    
    // Reflection
    vec3 reflection = reflect(I, N);
    vec3 reflectionColor = textureCube(cubemap, reflection).rgb;
    
    // Refraction
    vec3 refraction = refract(I, N, ratio);
    vec3 refractionColor = textureCube(cubemap, refraction).rgb;
    
    // Mix reflection and refraction based on fresnel
    vec3 finalColor = mix(refractionColor, reflectionColor, fresnel);
    
    // Add water color tint
    vec3 waterColor = vec3(0.0, 0.3, 0.5);
    finalColor = mix(finalColor, waterColor, 0.3);
    
    gl_FragColor = vec4(finalColor, 0.8);
}
"""

def compile_shader():
    vertex = shaders.compileShader(VERTEX_SHADER, GL_VERTEX_SHADER)
    fragment = shaders.compileShader(FRAGMENT_SHADER, GL_FRAGMENT_SHADER)
    return shaders.compileProgram(vertex, fragment)

# ---- Parametry fali radialnej ----
WAVELENGTH = 5.0
SPEED = 1.0

# Maksymalny czas życia ripple’a (w klatkach)
MAX_LIFETIME = 100

# Lista aktywnych „rippli” (fala radialna). Każdy to (x0, z0, t0, frame0)
ripples = []

# Licznik klatek (ticks). Zaczynamy od zera.
frame_count = 0

def base_wave_function(x, z, t):
    """Podstawowa fala (sin(x+t) * cos(z+t))."""
    return math.sin(x + t) * math.cos(z + t)

def radial_ripple_contribution(x, z, t, ripple):
    """
    Jeden „ripple” (fala radialna). 
    ripple = (x0, z0, t0, frame0).
    Wzór:
       r = sqrt((x - x0)^2 + (z - z0)^2)
       A = 1 / (1 + 0.1 * r)
       fala = A * sin(2π (r / WAVELENGTH − SPEED * (t − t0)))
    """
    x0, z0, t0, frame0 = ripple
    dt = t - t0
    if dt < 0:
        return 0.0
    dx = x - x0
    dz = z - z0
    r = math.sqrt(dx*dx + dz*dz)
    A = 1.0 / (1.0 + 0.1 * r)
    phase = 2 * math.pi * (r / WAVELENGTH - SPEED * dt)
    return A * math.sin(phase)

def combined_wave(x, z, t):
    """
    Suma podstawowej fali + wszystkich aktywnych „rippli”, 
    z liniowym wygaszaniem amplitudy ripple’a w ciągu MAX_LIFETIME klatek.
    """
    global ripples, frame_count
    y = base_wave_function(x, z, t)
    
    still_active = []
    for ripple in ripples:
        x0, z0, t0, frame0 = ripple
        age_frames = frame_count - frame0
        
        # Jeśli ripple nie przekroczył maksymalnej żywotności:
        if age_frames < MAX_LIFETIME:
            # Obliczamy „fade factor” liniowo malejący od 1.0 do 0.0
            fade = 1.0 - (age_frames / MAX_LIFETIME)
            contrib = radial_ripple_contribution(x, z, t, ripple)
            y += fade * contrib
            still_active.append(ripple)
        # Po MAX_LIFETIME klatkach ripple jest usuwane (nie kopiujemy do still_active)
    
    # Odświeżamy listę rippli
    ripples = still_active
    return y

def frange(start, stop, step):
    while start < stop:
        yield round(start, 5)
        start += step

def draw_water_reflective(size=100.0, time_val=0.0, grid_range=10, spacing=1.0):
    xs = list(frange(-grid_range, grid_range, spacing))
    zs = list(frange(-grid_range, grid_range, spacing))

    glUseProgram(shader_program)
    
    # Przekazanie uniformu „time”
    loc_time = glGetUniformLocation(shader_program, "time")
    glUniform1f(loc_time, time_val)
    
    # Bindowanie cubemap
    glActiveTexture(GL_TEXTURE0)
    glBindTexture(GL_TEXTURE_CUBE_MAP, skybox_tex)
    loc_cube = glGetUniformLocation(shader_program, "cubemap")
    glUniform1i(loc_cube, 0)

    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

    eps = spacing * 0.5  # mały krok do obliczeń pochodnych
    def normal_at(x, z):
        # dHeight/dx
        h_x1 = combined_wave(x + eps, z, time_val)
        h_x0 = combined_wave(x - eps, z, time_val)
        dx = (h_x1 - h_x0) / (2 * eps)
        # dHeight/dz
        h_z1 = combined_wave(x, z + eps, time_val)
        h_z0 = combined_wave(x, z - eps, time_val)
        dz = (h_z1 - h_z0) / (2 * eps)
        nx = -dx
        ny = 1.0
        nz = -dz
        length = math.sqrt(nx*nx + ny*ny + nz*nz)
        if length == 0:
            return (0.0, 1.0, 0.0)
        return (nx/length, ny/length, nz/length)

    glBegin(GL_TRIANGLES)
    for i in range(len(xs)-1):
        for j in range(len(zs)-1):
            x0, x1 = xs[i], xs[i+1]
            z0, z1 = zs[j], zs[j+1]

            # Wysokości w czterech rogach kwadratu
            y00 = combined_wave(x0, z0, time_val)
            y10 = combined_wave(x1, z0, time_val)
            y11 = combined_wave(x1, z1, time_val)
            y01 = combined_wave(x0, z1, time_val)

            n00 = normal_at(x0, z0)
            n10 = normal_at(x1, z0)
            n11 = normal_at(x1, z1)
            n01 = normal_at(x0, z1)

            sx0 = x0 * size / grid_range; sx1 = x1 * size / grid_range
            sz0 = z0 * size / grid_range; sz1 = z1 * size / grid_range

            # Pierwszy trójkąt
            glNormal3f(*n00); glVertex3f(sx0, y00, sz0)
            glNormal3f(*n10); glVertex3f(sx1, y10, sz0)
            glNormal3f(*n11); glVertex3f(sx1, y11, sz1)
            # Drugi trójkąt
            glNormal3f(*n00); glVertex3f(sx0, y00, sz0)
            glNormal3f(*n11); glVertex3f(sx1, y11, sz1)
            glNormal3f(*n01); glVertex3f(sx0, y01, sz1)
    glEnd()

    glDisable(GL_BLEND)
    glUseProgram(0)

# --------------------------------------------------------------------------------
#   Skybox (cubemap) loading & drawing
# --------------------------------------------------------------------------------
CUBE_MAP_DIR = "skybox"
CUBE_MAP_FACES = [
    ("woda2.png",  GL_TEXTURE_CUBE_MAP_POSITIVE_X),
    ("woda2.png",  GL_TEXTURE_CUBE_MAP_NEGATIVE_X),
    ("top2.jpg",     GL_TEXTURE_CUBE_MAP_POSITIVE_Y),
    ("bottom2.jpg",   GL_TEXTURE_CUBE_MAP_NEGATIVE_Y),
    ("woda2.png",  GL_TEXTURE_CUBE_MAP_POSITIVE_Z),
    ("woda2.png",  GL_TEXTURE_CUBE_MAP_NEGATIVE_Z),
]

def load_cubemap():
    tex = glGenTextures(1)
    glBindTexture(GL_TEXTURE_CUBE_MAP, tex)
    glPixelStorei(GL_UNPACK_ALIGNMENT, 1)

    size = 2048
    for fname, face in CUBE_MAP_FACES:
        path = os.path.join(CUBE_MAP_DIR, fname)
        surf = pygame.image.load(path).convert()
        surf = pygame.transform.smoothscale(surf, (size, size))
        data = pygame.image.tostring(surf, "RGB", True)
        glTexImage2D(face, 0, GL_RGB, size, size, 0, GL_RGB, GL_UNSIGNED_BYTE, data)

    glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
    glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
    glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_WRAP_R, GL_CLAMP_TO_EDGE)
    return tex

# --------------------------------------------------------------------------------
#   Poprawiona funkcja: „rozszerzony” skybox bez szczelin między ścianami
# --------------------------------------------------------------------------------
def draw_expanded_skybox(size=500.0, side_offset=500.0, center_y=0.0):
    """
    size         – połowa grubości ścianki w osi prostopadłej
    side_offset  – odległość od środka kostki w osiach X/Z
    center_y     – pozycja środka kostki w osi Y
    """

    glColor4f(1.0, 1.0, 1.0, 1.0)
    glDepthMask(GL_FALSE)
    glDisable(GL_LIGHTING)
    glEnable(GL_TEXTURE_CUBE_MAP)
    glBindTexture(GL_TEXTURE_CUBE_MAP, skybox_tex)

    cx, cy, cz = 0.0, center_y, 0.0
    over = 2.0
    ext = size + side_offset + over  # rozmiar rozszerzony

    def set_cube_texcoord_for_world_vertex(vx, vy, vz):
        dx, dy, dz = vx, vy, vz
        length = math.sqrt(dx*dx + dy*dy + dz*dz)
        if length == 0:
            glTexCoord3f(0.0, 0.0, 0.0)
        else:
            glTexCoord3f(dx / length, dy / length, dz / length)

    glBegin(GL_QUADS)
    # +X
    x0 = cx + ext
    for (dy, dz) in [(-ext, -ext), (-ext, +ext), (+ext, +ext), (+ext, -ext)]:
        vx, vy, vz = x0, cy + dy, cz + dz
        set_cube_texcoord_for_world_vertex(vx, vy, vz)
        glVertex3f(vx, vy, vz)
    # -X
    x0 = cx - ext
    for (dy, dz) in [(-ext, +ext), (-ext, -ext), (+ext, -ext), (+ext, +ext)]:
        vx, vy, vz = x0, cy + dy, cz + dz
        set_cube_texcoord_for_world_vertex(vx, vy, vz)
        glVertex3f(vx, vy, vz)
    # +Y
    y0 = cy + size + over
    for (dx, dz) in [(-ext, +ext), (-ext, -ext), (+ext, -ext), (+ext, +ext)]:
        vx, vy, vz = cx + dx, y0, cz + dz
        set_cube_texcoord_for_world_vertex(vx, vy, vz)
        glVertex3f(vx, vy, vz)
    # -Y
    y0 = cy - size - over
    for (dx, dz) in [(-ext, -ext), (+ext, -ext), (+ext, +ext), (-ext, +ext)]:
        vx, vy, vz = cx + dx, y0, cz + dz
        set_cube_texcoord_for_world_vertex(vx, vy, vz)
        glVertex3f(vx, vy, vz)
    # +Z
    z0 = cz + ext
    for (dx, dy) in [(-ext, -ext), (-ext, +ext), (+ext, +ext), (+ext, -ext)]:
        vx, vy, vz = cx + dx, cy + dy, z0
        set_cube_texcoord_for_world_vertex(vx, vy, vz)
        glVertex3f(vx, vy, vz)
    # -Z
    z0 = cz - ext
    for (dx, dy) in [(-ext, +ext), (+ext, +ext), (+ext, -ext), (-ext, -ext)]:
        vx, vy, vz = cx + dx, cy + dy, z0
        set_cube_texcoord_for_world_vertex(vx, vy, vz)
        glVertex3f(vx, vy, vz)
    glEnd()

    glDisable(GL_TEXTURE_CUBE_MAP)
    glEnable(GL_LIGHTING)
    glDepthMask(GL_TRUE)

# --------------------------------------------------------------------------------
#   Main application
# --------------------------------------------------------------------------------
def main():
    global skybox_tex, shader_program, frame_count, ripples

    pygame.init()
    screen_width, screen_height = 1280, 720
    pygame.display.set_mode((screen_width, screen_height), DOUBLEBUF | OPENGL)
    pygame.mouse.set_visible(True)  
    clock = pygame.time.Clock()

    glEnable(GL_DEPTH_TEST)
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    glEnable(GL_LIGHT1)

    skybox_tex = load_cubemap()
    shader_program = compile_shader()

    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(60, screen_width / screen_height, 0.1, 3000.0)

    yaw = pitch = 0.0
    time_val = 0.0

    rotating = False
    last_mouse_pos = (0, 0)
    mouse_sensitivity = 0.2

    # Główna pętla programu
    while True:
        for e in pygame.event.get():
            # Zamknięcie okna
            if e.type == QUIT:
                pygame.quit()
                return

            # ESC zamyka program
            if e.type == KEYDOWN and e.key == K_ESCAPE:
                pygame.quit()
                return

            # Przycisk prawej myszy: obrót kamery
            if e.type == MOUSEBUTTONDOWN and e.button == 3:
                rotating = True
                last_mouse_pos = pygame.mouse.get_pos()
            if e.type == MOUSEBUTTONUP and e.button == 3:
                rotating = False

            # Lewy przycisk myszy: dodajemy ripple w miejscu kliknięcia,
            # przechowując oprócz x0,z0 również time_val i frame_count
            if e.type == MOUSEBUTTONDOWN and e.button == 1:
                mx, my = pygame.mouse.get_pos()
                winX = mx
                winY = screen_height - my

                modelview = glGetDoublev(GL_MODELVIEW_MATRIX)
                projection = glGetDoublev(GL_PROJECTION_MATRIX)
                viewport = glGetIntegerv(GL_VIEWPORT)

                near = gluUnProject(winX, winY, 0.0, modelview, projection, viewport)
                far  = gluUnProject(winX, winY, 1.0, modelview, projection, viewport)

                nx, ny, nz = near
                fx, fy, fz = far
                dy_ray = fy - ny
                if abs(dy_ray) > 1e-6:
                    t_plane = (-60.0 - ny) / dy_ray
                    ix = nx + (fx - nx) * t_plane
                    iz = nz + (fz - nz) * t_plane
                    # Przeliczamy na „grid coordinates”
                    xg = ix / (80.0 / 10)
                    zg = iz / (80.0 / 10)
                    ripples.append((xg, zg, time_val, frame_count))

        # Obrót kamery (mysz prawy przycisk)
        if rotating:
            mx, my = pygame.mouse.get_pos()
            dx = mx - last_mouse_pos[0]
            dy = my - last_mouse_pos[1]
            yaw   += dx * mouse_sensitivity
            pitch += dy * mouse_sensitivity
            pitch = max(-89, min(89, pitch))
            last_mouse_pos = (mx, my)

        # Sterowanie klawiaturą (strzałki)
        keys = pygame.key.get_pressed()
        if keys[K_LEFT]:   yaw   -= 1.0
        if keys[K_RIGHT]:  yaw   += 1.0
        if keys[K_UP]:     pitch -= 1.0
        if keys[K_DOWN]:   pitch += 1.0
        pitch = max(-89, min(89, pitch))

        # Ustawienia kamery
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glRotatef(pitch, 1, 0, 0)
        glRotatef(yaw,   0, 1, 0)

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        # === RYSUJEMY SKYBOX ===
        draw_expanded_skybox(size=500.0, side_offset=500.0, center_y=0.0)

        # === RYSUJEMY WODĘ ===
        glDisable(GL_LIGHTING)
        glPushMatrix()
        # Przesuwamy wodę w dół o 60 jednostek (płaszczyzna y = -60)
        glTranslatef(0, -35, 0)
        draw_water_reflective(size=80.0, time_val=time_val, grid_range=10, spacing=1.0)
        glPopMatrix()
        glEnable(GL_LIGHTING)

        pygame.display.flip()
        clock.tick(60)

        # Po każdym rysowaniu: zwiększamy czas i licznik klatek
        time_val += 0.03   # animacja „przepływu” czasu
        frame_count += 1   # o jeden tick więcej

if __name__ == "__main__":
    main()
