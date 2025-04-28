""""
1. Stwórz podstawową scenę
Zainicjuj OpenGL (np. przy pomocy GLFW + GLAD).

Stwórz prostą siatkę (np. płaski prostokąt złożony z kilku wierzchołków) reprezentującą wodę.

Dodaj podstawową kamerę 3D (sterowaną myszką i klawiaturą).

➡️ Cel: mieć możliwość latania nad "pustym" płaskim prostokątem.

2. Przygotuj "Render to Texture" (FBO)
Utwórz Framebuffer Object (FBO).

Podłącz do niego teksturę koloru (np. GL_COLOR_ATTACHMENT0) i renderbuffer głębi (dla GL_DEPTH_ATTACHMENT).

Przygotuj 2 osobne FBO:

jedno dla refleksji (odbicie),

jedno dla refrakcji (załamanie).

➡️ Cel: nauczyć się renderować obraz sceny do tekstury, nie na ekran.

3. Woda: podstawowe renderowanie
Przygotuj prosty shader dla powierzchni wody.

Na razie wyświetl teksturę (z refleksji lub refrakcji) na powierzchni wody.

➡️ Cel: mieć „działającą” wodę z teksturą.

4. Refleksja i refrakcja
Refleksja:

Odwróć kamerę względem poziomu wody (np. odbicie osi Y).

Renderuj scenę do tekstury refleksji.

Refrakcja:

Renderuj tylko te fragmenty sceny, które są pod powierzchnią wody (np. za pomocą prostego clipping plane).

Wynik wrzuć do tekstury refrakcji.

➡️ Cel: mieć dwie osobne tekstury: odbicie nad wodą i refrakcję pod wodą.

5. Woda: efekt falowania
Dodaj ruchomą normal mapę (lub generuj przesunięcia UV).

W shaderze wody:

Lekko przesuwaj współrzędne tekstury w czasie (time uniform).

Zmieniaj normalne, by efekt był bardziej dynamiczny.

➡️ Cel: powierzchnia wody zacznie falować i załamywać światło.

6. Podstawowy shader wody
Shader fragmentu (fragment shader) dla wody powinien:

Odczytać kolor z tekstury refleksji i refrakcji.

Użyć normal mapy do zmodyfikowania współrzędnych odczytu (symulacja fal).

Wymieszać kolory refleksji i refrakcji (proporcjonalnie do kąta patrzenia).
""""
import glfw
from OpenGL.GL import *
import numpy as np

# Inicjalizacja GLFW
if not glfw.init():
    raise Exception("GLFW can't be initialized")

# Tworzenie okna
window = glfw.create_window(800, 600, "Woda w OpenGL", None, None)
if not window:
    glfw.terminate()
    raise Exception("GLFW window can't be created")

glfw.make_context_current(window)

# Ustawienia OpenGL
glClearColor(0.2, 0.3, 0.3, 1)
glEnable(GL_DEPTH_TEST)

# Wierzchołki wody (płaski prostokąt)
water_vertices = np.array([
    -1.0, 0.0, -1.0,
     1.0, 0.0, -1.0,
     1.0, 0.0,  1.0,
    
    -1.0, 0.0, -1.0,
     1.0, 0.0,  1.0,
    -1.0, 0.0,  1.0
], dtype=np.float32)

# Tworzenie VAO i VBO
VAO = glGenVertexArrays(1)
VBO = glGenBuffers(1)

glBindVertexArray(VAO)

glBindBuffer(GL_ARRAY_BUFFER, VBO)
glBufferData(GL_ARRAY_BUFFER, water_vertices.nbytes, water_vertices, GL_STATIC_DRAW)

glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 0, None)
glEnableVertexAttribArray(0)

# Odwiązanie
glBindBuffer(GL_ARRAY_BUFFER, 0)
glBindVertexArray(0)

# Shader do wody
vertex_shader = """
#version 330
layout (location = 0) in vec3 aPos;

uniform mat4 model;
uniform mat4 view;
uniform mat4 projection;

void main()
{
    gl_Position = projection * view * model * vec4(aPos, 1.0);
}
"""

fragment_shader = """
#version 330
out vec4 FragColor;

void main()
{
    FragColor = vec4(0.0, 0.4, 0.7, 1.0); // kolor wody
}
"""

def compile_shader(source, shader_type):
    shader = glCreateShader(shader_type)
    glShaderSource(shader, source)
    glCompileShader(shader)
    if not glGetShaderiv(shader, GL_COMPILE_STATUS):
        raise Exception(glGetShaderInfoLog(shader))
    return shader

def create_shader_program():
    program = glCreateProgram()
    vs = compile_shader(vertex_shader, GL_VERTEX_SHADER)
    fs = compile_shader(fragment_shader, GL_FRAGMENT_SHADER)
    glAttachShader(program, vs)
    glAttachShader(program, fs)
    glLinkProgram(program)
    if not glGetProgramiv(program, GL_LINK_STATUS):
        raise Exception(glGetProgramInfoLog(program))
    glDeleteShader(vs)
    glDeleteShader(fs)
    return program

shader_program = create_shader_program()

# Proste macierze (brak biblioteki glm, robimy ręcznie)
import glm
projection = glm.perspective(glm.radians(45), 800/600, 0.1, 100)
view = glm.lookAt(glm.vec3(0, 2, 4), glm.vec3(0, 0, 0), glm.vec3(0, 1, 0))
model = glm.mat4(1.0)

# Główna pętla
while not glfw.window_should_close(window):
    glfw.poll_events()

    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    glUseProgram(shader_program)

    # Ustawienie macierzy
    loc_model = glGetUniformLocation(shader_program, "model")
    loc_view = glGetUniformLocation(shader_program, "view")
    loc_projection = glGetUniformLocation(shader_program, "projection")

    glUniformMatrix4fv(loc_model, 1, GL_FALSE, glm.value_ptr(model))
    glUniformMatrix4fv(loc_view, 1, GL_FALSE, glm.value_ptr(view))
    glUniformMatrix4fv(loc_projection, 1, GL_FALSE, glm.value_ptr(projection))

    glBindVertexArray(VAO)
    glDrawArrays(GL_TRIANGLES, 0, 6)

    glfw.swap_buffers(window)

# Sprzątanie
glDeleteVertexArrays(1, [VAO])
glDeleteBuffers(1, [VBO])
glfw.terminate()
