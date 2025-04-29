import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *


def draw_axes():
    glBegin(GL_LINES)

    # Oś X - czerwona
    glColor3f(1, 0, 0)
    glVertex3f(-2, 0, 0)
    glVertex3f(2, 0, 0)

    # Oś Y - zielona
    glColor3f(0, 1, 0)
    glVertex3f(0, -2, 0)
    glVertex3f(0, 2, 0)

    # Oś Z - niebieska
    glColor3f(0, 0, 1)
    glVertex3f(0, 0, -2)
    glVertex3f(0, 0, 2)

    glEnd()



def main():
    pygame.init()
    display = (800, 600)
    pygame.display.set_mode(display, DOUBLEBUF | OPENGL)


    clock = pygame.time.Clock()

    gluPerspective(45, (display[0] / display[1]), 0.1, 50.0)
    glTranslatef(0.0,0.0, -5)

    while True:
        for event in pygame.event.get():
            if event.type == QUIT:
                return


        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)#przygotowuje bufor do rysowania

        glPushMatrix()# Zachowaj macierz transformacji
        glRotatef(30, 1, 0, 0)
        glRotatef(30, 0, 1, 0)
        draw_axes()

        glPointSize(10)  # Ustawia rozmiar punktów na 10 pikseli

        glBegin(GL_POINTS)
        glColor3f(1, 1, 1)#ustawia kolor rysowania argumenty RGB
        glVertex3f(-1, 0, -1)
        glVertex3f(0, 0, -1)
        glVertex3f(1, 0, -1)
        glVertex3f(1, 0, 0)
        glVertex3f(0, 0, 0) #w układzie xyz rysuje punkty
        glVertex3f(-1, 0, 0)
        glVertex3f(-1, 0, 1)
        glVertex3f(0, 0, 1)
        glVertex3f(1, 0, 1)
        glEnd()
        glPopMatrix()# Przywróć macierz

        pygame.display.flip()
        clock.tick(60)

if __name__ == "__main__":
    main()
