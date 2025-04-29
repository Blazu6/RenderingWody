import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import math

def wave_function(x, z, time):
    return math.sin(x + time) * math.cos(z + time)

def draw_axes():
    glBegin(GL_LINES)
    glColor3f(1, 0, 0)  # X axis - red
    glVertex3f(-2, 0, 0)
    glVertex3f(2, 0, 0)

    glColor3f(0, 1, 0)  # Y axis - green
    glVertex3f(0, -2, 0)
    glVertex3f(0, 2, 0)

    glColor3f(0, 0, 1)  # Z axis - blue
    glVertex3f(0, 0, -2)
    glVertex3f(0, 0, 2)
    glEnd()

def frange(start, stop, step):
    while start < stop:
        yield round(start, 5)  # zaokrąglamy, by uniknąć błędów zmiennoprzecinkowych
        start += step

def main():
    pygame.init()
    display = (800, 600)
    pygame.display.set_mode(display, DOUBLEBUF | OPENGL)
    clock = pygame.time.Clock()

    gluPerspective(45, (display[0] / display[1]), 0.1, 50.0)
    glTranslatef(0.0, 0.0, -15)

    time = 0
    grid_range = 5  # siatka od -5 do 5
    spacing = 0.5   # gęstość siatki

    # Pre-wygeneruj współrzędne X i Z
    x_coords = list(frange(-grid_range, grid_range, spacing))
    z_coords = list(frange(-grid_range, grid_range, spacing))

    while True:
        for event in pygame.event.get():
            if event.type == QUIT:
                return

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glPushMatrix()
        glRotatef(30, 1, 0, 0)
        glRotatef(30, 0, 1, 0)
        draw_axes()

        # --- Generowanie siatki punktów z y uzależnionym od wave_function
        points = []
        for x in x_coords:
            row = []
            for z in z_coords:
                y = wave_function(x, z, time)
                row.append((x, y, z))
            points.append(row)

        # --- Rysowanie punktów
        glPointSize(5)
        glBegin(GL_POINTS)
        glColor3f(1, 1, 1)
        for row in points:
            for p in row:
                glVertex3fv(p)
        glEnd()

        # --- Rysowanie powierzchni jako siatka z trójkątów
        glBegin(GL_TRIANGLES)
        glColor3f(0.3, 0.7, 1)
        for i in range(len(points) - 1):
            for j in range(len(points[i]) - 1):
                A = points[i][j]
                B = points[i+1][j]
                C = points[i+1][j+1]
                D = points[i][j+1]

                # Trójkąty
                glVertex3fv(A)
                glVertex3fv(B)
                glVertex3fv(C)

                glVertex3fv(A)
                glVertex3fv(C)
                glVertex3fv(D)
        glEnd()

        glPopMatrix()
        time += 0.03

        pygame.display.flip()
        clock.tick(60)

if __name__ == "__main__":
    main()
