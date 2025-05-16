import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import math

def wave_function(x, z, time):
    return math.sin(x + time) * math.cos(z + time)

def draw_axes():
    glBegin(GL_LINES)
    glColor3f(1, 0, 0); glVertex3f(-2, 0, 0); glVertex3f(2, 0, 0)
    glColor3f(0, 1, 0); glVertex3f(0, -2, 0); glVertex3f(0, 2, 0)
    glColor3f(0, 0, 1); glVertex3f(0, 0, -2); glVertex3f(0, 0, 2)
    glEnd()

def frange(start, stop, step):
    while start < stop:
        yield round(start, 5)
        start += step

def init_lighting():
    # Włącz oświetlenie
    glEnable(GL_LIGHTING)
    # Główne źródło światła (zewnętrzne, np. rozproszone niebo)
    glEnable(GL_LIGHT0)
    ambient0 = [0.2, 0.2, 0.2, 1.0]
    diffuse0 = [1.0, 1.0, 1.0, 1.0]
    specular0 = [1.0, 1.0, 1.0, 1.0]
    glLightfv(GL_LIGHT0, GL_AMBIENT, ambient0)
    glLightfv(GL_LIGHT0, GL_DIFFUSE, diffuse0)
    glLightfv(GL_LIGHT0, GL_SPECULAR, specular0)
    # Dodatkowe źródło – słońce jako światło kierunkowe
    glEnable(GL_LIGHT1)
    ambient1 = [0.0, 0.0, 0.0, 1.0]
    diffuse1 = [1.0, 0.9, 0.6, 1.0]  # ciepły odcień
    specular1 = [1.0, 1.0, 1.0, 1.0]
    glLightfv(GL_LIGHT1, GL_AMBIENT, ambient1)
    glLightfv(GL_LIGHT1, GL_DIFFUSE, diffuse1)
    glLightfv(GL_LIGHT1, GL_SPECULAR, specular1)
    # materiały przez glColor
    glEnable(GL_COLOR_MATERIAL)
    glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)

    # Podwyższona połyskliwość dla wody
    glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, [1.0, 1.0, 1.0, 1.0])
    glMaterialf(GL_FRONT_AND_BACK, GL_SHININESS, 64.0)

def main():
    pygame.init()
    display = (800, 600)
    pygame.display.set_mode(display, DOUBLEBUF | OPENGL)
    clock = pygame.time.Clock()

    gluPerspective(45, display[0] / display[1], 0.1, 100.0)
    cam_x, cam_y, cam_z = 0.0, 0.0, -15.0
    yaw, pitch = 0.0, 30.0
    move_speed, rot_speed = 0.3, 1.5

    init_lighting()

    rotating = False
    last_mouse = (0, 0)
    mouse_sensitivity = 0.2

    time_val = 0.0
    grid_range, spacing = 5, 0.5
    x_coords = list(frange(-grid_range, grid_range, spacing))
    z_coords = list(frange(-grid_range, grid_range, spacing))

    while True:
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                return
            if event.type == MOUSEBUTTONDOWN and event.button == 3:
                rotating = True
                last_mouse = event.pos
            if event.type == MOUSEBUTTONUP and event.button == 3:
                rotating = False
            if event.type == MOUSEMOTION and rotating:
                dx, dy = event.pos[0] - last_mouse[0], event.pos[1] - last_mouse[1]
                yaw   += dx * mouse_sensitivity
                pitch += dy * mouse_sensitivity
                pitch = max(-89, min(89, pitch))
                last_mouse = event.pos

        keys = pygame.key.get_pressed()
        if keys[K_LEFT]:  cam_x += move_speed
        if keys[K_RIGHT]: cam_x -= move_speed
        if keys[K_UP]:    cam_y -= move_speed
        if keys[K_DOWN]:  cam_y += move_speed
        if keys[K_w]:     cam_z += move_speed
        if keys[K_s]:     cam_z -= move_speed
        if keys[K_q]:     yaw   += rot_speed
        if keys[K_e]:     yaw   -= rot_speed

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        glPushMatrix()
        glTranslatef(cam_x, cam_y, cam_z)
        glRotatef(yaw,   0, 1, 0)
        glRotatef(pitch, 1, 0, 0)

        # Ustawienie pozycji świateł
        glLightfv(GL_LIGHT0, GL_POSITION, [0.0, 5.0, 0.0, 1.0])
        # kierunkowe jako od słońca z tyłu/skrótu
        glLightfv(GL_LIGHT1, GL_POSITION, [-1.0, 1.0, 0.0, 0.0])

        draw_axes()

        points = []
        for x in x_coords:
            row = []
            for z in z_coords:
                y = wave_function(x, z, time_val)
                row.append((x, y, z))
            points.append(row)

        # rysowanie wody z refleksami
        glPushMatrix()
        glTranslatef(0, -0.1, 0)
        layers = [
            (-0.05, 0.3, lambda f: (0.2, 0.6 * f, 1.0 * f)),
            (-0.15, 0.6, lambda f: (0.1, 0.4 * f, 0.8 * f)),
            (-0.30, 1.0, lambda f: (0.05, 0.2 * f, 0.5 * f)),
        ]
        maxd = math.hypot(grid_range, grid_range)
        for y_off, alpha, color_func in layers:
            glPushMatrix()
            glTranslatef(0, y_off, 0)
            glBegin(GL_TRIANGLES)
            for i in range(len(points)-1):
                for j in range(len(points[i])-1):
                    A = points[i][j]; B = points[i+1][j]
                    C = points[i+1][j+1]; D = points[i][j+1]
                    for tri in [(A, B, C), (A, C, D)]:
                        for p in tri:
                            dist = math.hypot(p[0], p[2])
                            f = 1 - dist/maxd
                            # kolor podstawowy
                            glColor4f(*color_func(f), alpha)
                            glVertex3fv(p)
            glEnd()
            glPopMatrix()
        glPopMatrix()

        glPopMatrix()
        pygame.display.flip()
        clock.tick(60)
        time_val += 0.03

if __name__ == "__main__":
    main()
