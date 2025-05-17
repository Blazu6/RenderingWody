import os
import math
import random

import pygame
from pygame.locals import DOUBLEBUF, OPENGL, QUIT, KEYDOWN, K_ESCAPE, K_LEFT, K_RIGHT, K_UP, K_DOWN, MOUSEBUTTONDOWN, MOUSEBUTTONUP

from OpenGL.GL import *
from OpenGL.GLU import gluPerspective
from OpenGL.GL import shaders

# --------------------------------------------------------------------------------
#   Wave & water with animated cubemap reflection and refraction
# --------------------------------------------------------------------------------
random.seed(0)

# Vertex shader for water effects
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

# Fragment shader for water effects
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

def wave_function(x, z, t):
    return math.sin(x + t) * math.cos(z + t)

def frange(start, stop, step):
    while start < stop:
        yield round(start, 5)
        start += step

def draw_water_reflective(size=100.0, time_val=0.0, grid_range=10, spacing=1.0):
    xs = list(frange(-grid_range, grid_range, spacing))
    zs = list(frange(-grid_range, grid_range, spacing))

    # Use shader program
    glUseProgram(shader_program)
    
    # Set time uniform
    loc_time = glGetUniformLocation(shader_program, "time")
    glUniform1f(loc_time, time_val)
    
    # Bind cubemap texture
    glActiveTexture(GL_TEXTURE0)
    glBindTexture(GL_TEXTURE_CUBE_MAP, skybox_tex)
    loc_cube = glGetUniformLocation(shader_program, "cubemap")
    glUniform1i(loc_cube, 0)

    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

    eps = spacing
    def normal_at(x, z):
        dx = (wave_function(x+eps, z, time_val) - wave_function(x-eps, z, time_val)) / (2*eps)
        dz = (wave_function(x, z+eps, time_val) - wave_function(x, z-eps, time_val)) / (2*eps)
        nx, ny, nz = -dx, 1.0, -dz
        jitter = math.sin(x*12 + z*9 + time_val*6) * 0.1
        nx += jitter
        nz += jitter
        L = math.sqrt(nx*nx + ny*ny + nz*nz)
        return (nx/L, ny/L, nz/L)

    glBegin(GL_TRIANGLES)
    for i in range(len(xs)-1):
        for j in range(len(zs)-1):
            x0, x1 = xs[i], xs[i+1]
            z0, z1 = zs[j], zs[j+1]

            y00 = wave_function(x0, z0, time_val)
            y10 = wave_function(x1, z0, time_val)
            y11 = wave_function(x1, z1, time_val)
            y01 = wave_function(x0, z1, time_val)

            n00 = normal_at(x0, z0)
            n10 = normal_at(x1, z0)
            n11 = normal_at(x1, z1)
            n01 = normal_at(x0, z1)

            sx0 = x0 * size / grid_range; sx1 = x1 * size / grid_range
            sz0 = z0 * size / grid_range; sz1 = z1 * size / grid_range

            # first triangle
            glNormal3f(*n00); glVertex3f(sx0, y00, sz0)
            glNormal3f(*n10); glVertex3f(sx1, y10, sz0)
            glNormal3f(*n11); glVertex3f(sx1, y11, sz1)
            # second triangle
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
    ("right.jpg",  GL_TEXTURE_CUBE_MAP_POSITIVE_X),
    ("left.jpg",   GL_TEXTURE_CUBE_MAP_NEGATIVE_X),
    ("top2.jpg",   GL_TEXTURE_CUBE_MAP_POSITIVE_Y),
    ("bottom.jpg", GL_TEXTURE_CUBE_MAP_NEGATIVE_Y),
    ("front.jpg",  GL_TEXTURE_CUBE_MAP_POSITIVE_Z),
    ("back.jpg",   GL_TEXTURE_CUBE_MAP_NEGATIVE_Z),
]

def load_cubemap():
    tex = glGenTextures(1)
    glBindTexture(GL_TEXTURE_CUBE_MAP, tex)
    glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
    size = 1024
    for fname, face in CUBE_MAP_FACES:
        path = os.path.join(CUBE_MAP_DIR, fname)
        surf = pygame.image.load(path).convert()
        surf = pygame.transform.smoothscale(surf, (size, size))
        data = pygame.image.tostring(surf, "RGB", True)
        glTexImage2D(face, 0, GL_RGB, size, size, 0, GL_RGB, GL_UNSIGNED_BYTE, data)
    for p in (GL_TEXTURE_MIN_FILTER, GL_TEXTURE_MAG_FILTER):
        glTexParameteri(GL_TEXTURE_CUBE_MAP, p, GL_LINEAR)
    for w in (GL_TEXTURE_WRAP_S, GL_TEXTURE_WRAP_T, GL_TEXTURE_WRAP_R):
        glTexParameteri(GL_TEXTURE_CUBE_MAP, w, GL_CLAMP_TO_EDGE)
    return tex

def draw_skybox(size=100.0):
    glColor4f(1.0, 1.0, 1.0, 1.0)
    glDepthMask(GL_FALSE)
    glDisable(GL_LIGHTING)
    glEnable(GL_TEXTURE_CUBE_MAP)
    glBindTexture(GL_TEXTURE_CUBE_MAP, skybox_tex)

    glBegin(GL_QUADS)
    # +X
    glTexCoord3f( 1,-1,-1); glVertex3f( size,-size,-size)
    glTexCoord3f( 1, 1,-1); glVertex3f( size, size,-size)
    glTexCoord3f( 1, 1, 1); glVertex3f( size, size, size)
    glTexCoord3f( 1,-1, 1); glVertex3f( size,-size, size)
    # -X
    glTexCoord3f(-1,-1, 1); glVertex3f(-size,-size, size)
    glTexCoord3f(-1, 1, 1); glVertex3f(-size, size, size)
    glTexCoord3f(-1, 1,-1); glVertex3f(-size, size,-size)
    glTexCoord3f(-1,-1,-1); glVertex3f(-size,-size,-size)
    # +Y
    glTexCoord3f(-1, 1,-1); glVertex3f(-size, size,-size)
    glTexCoord3f(-1, 1, 1); glVertex3f(-size, size, size)
    glTexCoord3f( 1, 1, 1); glVertex3f( size, size, size)
    glTexCoord3f( 1, 1,-1); glVertex3f( size, size,-size)
    # -Y
    glTexCoord3f(-1,-1, 1); glVertex3f(-size,-size, size)
    glTexCoord3f( 1,-1, 1); glVertex3f( size,-size, size)
    glTexCoord3f( 1,-1,-1); glVertex3f( size,-size,-size)
    glTexCoord3f(-1,-1,-1); glVertex3f(-size,-size,-size)
    # +Z
    glTexCoord3f(-1,-1, 1); glVertex3f(-size,-size, size)
    glTexCoord3f(-1, 1, 1); glVertex3f(-size, size, size)
    glTexCoord3f( 1, 1, 1); glVertex3f( size, size, size)
    glTexCoord3f( 1,-1, 1); glVertex3f( size,-size, size)
    # -Z
    glTexCoord3f( 1,-1,-1); glVertex3f( size,-size,-size)
    glTexCoord3f( 1, 1,-1); glVertex3f( size, size,-size)
    glTexCoord3f(-1, 1,-1); glVertex3f(-size, size,-size)
    glTexCoord3f(-1,-1,-1); glVertex3f(-size,-size,-size)
    glEnd()

    glDisable(GL_TEXTURE_CUBE_MAP)
    glEnable(GL_LIGHTING)
    glDepthMask(GL_TRUE)

# --------------------------------------------------------------------------------
#   Main application
# --------------------------------------------------------------------------------
def main():
    global skybox_tex, shader_program

    pygame.init()
    pygame.display.set_mode((800, 600), DOUBLEBUF | OPENGL)
    pygame.mouse.set_visible(False)
    clock = pygame.time.Clock()

    glEnable(GL_DEPTH_TEST)
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    glEnable(GL_LIGHT1)

    skybox_tex = load_cubemap()
    shader_program = compile_shader()

    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(60, 800/600, 0.1, 200.0)

    yaw = pitch = 0.0
    time_val = 0.0

    rotating = False
    last_mouse_pos = (0, 0)
    mouse_sensitivity = 0.2

    while True:
        for e in pygame.event.get():
            if e.type in (QUIT, KEYDOWN) and getattr(e, 'key', None) == K_ESCAPE:
                pygame.quit()
                return
            if e.type == MOUSEBUTTONDOWN and e.button == 3:  # right button down
                rotating = True
                last_mouse_pos = pygame.mouse.get_pos()
            if e.type == MOUSEBUTTONUP and e.button == 3:    # right button up
                rotating = False

        # only rotate when right button is held
        if rotating:
            mx, my = pygame.mouse.get_pos()
            dx = mx - last_mouse_pos[0]
            dy = my - last_mouse_pos[1]
            yaw   += dx * mouse_sensitivity
            pitch += dy * mouse_sensitivity
            pitch = max(-89, min(89, pitch))
            last_mouse_pos = (mx, my)

        # keyboard panning
        keys = pygame.key.get_pressed()
        if keys[K_LEFT]:   yaw   -= 1.0
        if keys[K_RIGHT]:  yaw   += 1.0
        if keys[K_UP]:     pitch -= 1.0
        if keys[K_DOWN]:   pitch += 1.0
        pitch = max(-89, min(89, pitch))

        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glRotatef(pitch, 1, 0, 0)
        glRotatef(yaw,   0, 1, 0)

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        # draw skybox
        draw_skybox(100.0)

        # draw reflective water
        glDisable(GL_LIGHTING)
        glPushMatrix()
        glTranslatef(0, -50, 0)
        draw_water_reflective(size=100.0, time_val=time_val)
        glPopMatrix()
        glEnable(GL_LIGHTING)

        pygame.display.flip()
        clock.tick(60)
        time_val += 0.03

if __name__ == "__main__":
    main()
