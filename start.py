import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import math

def wave_function(x, z, time):
    return math.sin(x + time) * math.cos(z + time)

def draw_axes():
    glBegin(GL_LINES)
    # oś X – czerwona
    glColor3f(1, 0, 0)
    glVertex3f(-2, 0, 0)
    glVertex3f(2, 0, 0)
    # oś Y – zielona
    glColor3f(0, 1, 0)
    glVertex3f(0, -2, 0)
    glVertex3f(0, 2, 0)
    # oś Z – niebieska
    glColor3f(0, 0, 1)
    glVertex3f(0, 0, -2)
    glVertex3f(0, 0, 2)
    glEnd()

def frange(start, stop, step):
    while start < stop:
        yield round(start, 5)
        start += step

def main():
    pygame.init()
    display = (800, 600)
    pygame.display.set_mode(display, DOUBLEBUF | OPENGL)
    clock = pygame.time.Clock()

    gluPerspective(45, display[0]/display[1], 0.1, 100.0)

    # pozycja i obrót kamery
    cam_x, cam_y, cam_z = 0.0, 0.0, -15.0
    rot_y = 0.0  # obrót kamery wokół osi Y
    move_speed = 0.3
    rot_speed = 1.5  # stopnie na klatkę

    time = 0
    grid_range = 5
    spacing = 0.5
    x_coords = list(frange(-grid_range, grid_range, spacing))
    z_coords = list(frange(-grid_range, grid_range, spacing))

    while True:
        for event in pygame.event.get():
            if event.type == QUIT:
                return

        keys = pygame.key.get_pressed()
        # przesunięcia
        if keys[K_LEFT]:
            cam_x += move_speed
        if keys[K_RIGHT]:
            cam_x -= move_speed
        if keys[K_UP]:
            cam_y -= move_speed
        if keys[K_DOWN]:
            cam_y += move_speed
        if keys[K_w]:
            cam_z += move_speed
        if keys[K_s]:
            cam_z -= move_speed
        # obrót lewo/prawo
        if keys[K_q]:
            rot_y += rot_speed
        if keys[K_e]:
            rot_y -= rot_speed

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glPushMatrix()

        # najpierw przesuwamy/cam, potem obracamy
        glTranslatef(cam_x, cam_y, cam_z)
        glRotatef(rot_y, 0, 1, 0)
        # stały podgląd z góry – opcjonalnie zostawić albo usunąć
        glRotatef(30, 1, 0, 0)

        draw_axes()

        # generowanie siatki punktów
        points = []
        for x in x_coords:
            row = []
            for z in z_coords:
                y = wave_function(x, z, time)
                row.append((x, y, z))
            points.append(row)

        # rysowanie punktów
        glPointSize(5)
        glBegin(GL_POINTS)
        glColor3f(1, 1, 1)
        for row in points:
            for p in row:
                glVertex3fv(p)
        glEnd()

        # rysowanie powierzchni trójkątami
        glBegin(GL_TRIANGLES)
        glColor3f(0.3, 0.7, 1)
        for i in range(len(points)-1):
            for j in range(len(points[i]) - 1):
                A = points[i][j]
                B = points[i+1][j]
                C = points[i+1][j+1]
                D = points[i][j+1]
                glVertex3fv(A); glVertex3fv(B); glVertex3fv(C)
                glVertex3fv(A); glVertex3fv(C); glVertex3fv(D)
        glEnd()

        glPopMatrix()
        time += 0.03

        pygame.display.flip()
        clock.tick(60)

if __name__ == "__main__":
    main()
