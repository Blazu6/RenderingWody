# RenderingWody - Dokumentacja

## Funkcje OpenGL

### 1. `glPushMatrix()`
- **Opis**: Zapisuje aktualny stan macierzy transformacji. Dzięki temu możemy tymczasowo wprowadzić transformację, a później przywrócić poprzedni stan macierzy.
- **Zastosowanie**: Używamy jej, gdy chcemy wykonać jakąś transformację (np. obrót, przesunięcie), ale po jej wykonaniu wrócić do poprzedniego stanu transformacji.

### 2. `glPopMatrix()`
- **Opis**: Przywraca wcześniej zapisany stan macierzy transformacji (poprzez `glPushMatrix()`).
- **Zastosowanie**: Po zakończeniu transformacji używamy `glPopMatrix()`, aby powrócić do poprzedniego stanu, np. po obrocie obiektu.

### 3. `glRotatef(angle, x, y, z)`
- **Opis**: Obraca obiekt o zadany kąt (w stopniach) wokół osi określonej przez wektor (x, y, z).
- **Zastosowanie**: Używamy tej funkcji do obracania obiektów w przestrzeni 3D. Na przykład:
  - `glRotatef(30, 1, 0, 0)` — obraca obiekt o 30° wokół osi X.
  - `glRotatef(30, 0, 1, 0)` — obraca obiekt o 30° wokół osi Y.

### 4. `glBegin(mode)`
- **Opis**: Inicjalizuje rysowanie obiektów w OpenGL, określając tryb rysowania. Tryb może być różny (np. punkty, linie, trójkąty).
- **Zastosowanie**: Na początku rysowania musimy wybrać tryb (np. `GL_POINTS`, `GL_LINES`, `GL_TRIANGLES`) i rozpocząć rysowanie punktów lub obiektów.

### 5. `glEnd()`
- **Opis**: Kończy proces rysowania obiektów. Wszystko, co zostało zdefiniowane pomiędzy `glBegin()` i `glEnd()`, zostanie narysowane.
- **Zastosowanie**: Zawsze musimy użyć `glEnd()`, aby zakończyć definiowanie obiektów do narysowania po użyciu `glBegin()`.

### 6. `glVertex3f(x, y, z)`
- **Opis**: Określa jeden punkt w przestrzeni 3D, który ma być narysowany.
- **Zastosowanie**: Ta funkcja jest używana do określania punktów (współrzędnych) w przestrzeni 3D. Na przykład:
  - `glVertex3f(0, 0, 0)` — określa punkt w środku układu współrzędnych.

### 7. `glColor3f(r, g, b)`
- **Opis**: Ustawia kolor dla następnych rysowanych obiektów w przestrzeni 3D.
- **Zastosowanie**: Określamy kolor obiektów (np. punkty, linie) przed ich narysowaniem. Kolor podajemy w formacie RGB (każda składowa od 0 do 1).
  - `glColor3f(1, 0, 0)` — ustawia kolor na czerwony (R=1, G=0, B=0).

### 8. `glTranslatef(x, y, z)`
- **Opis**: Przesuwa obiekt o wektor (x, y, z) w przestrzeni 3D.
- **Zastosowanie**: Używamy tej funkcji, aby przesunąć obiekt w przestrzeni, np. aby ustawić punkt w odpowiedniej odległości od kamery.

### 9. `glPointSize(size)`
- **Opis**: Określa rozmiar rysowanych punktów.
- **Zastosowanie**: Używamy tej funkcji, aby ustawić rozmiar punktów, np. `glPointSize(10)` ustawi punkty na większe.

---

## Kolejne kroki - Symulacja falowania wody

### 1. Zrozumienie układu współrzędnych 3D (XYZ)
- W OpenGL przestrzeń 3D jest reprezentowana przez współrzędne \( x \), \( y \), i \( z \), gdzie:
  - **X** to oś pozioma (lewo-prawo).
  - **Y** to oś pionowa (góra-dół).
  - **Z** to oś głębokości (przód-tył).
- Podstawowy punkt w OpenGL ma współrzędne \( (x, y, z) \), a te punkty można używać do rysowania obiektów w przestrzeni.
- Funkcja fali – y = sin(x + t) * cos(z + t) dla animacji.
-Aktualizacja – w każdej klatce zmieniamy wysokość wierzchołków wg funkcji.
-Oświetlenie – włącz GL_LIGHTING, GL_LIGHT0, GL_LIGHT1, ustaw materiały i światła.

### 2. Rysowanie siatki punktów (mesh)
Aby stworzyć płaską powierzchnię, możesz rysować punkty w regularnych odstępach i łączyć je w trójkąty, tworząc siatkę (mesh). Można to zrobić za pomocą `glVertex3f()`, aby określić punkty w przestrzeni 3D.

Przykładowo:
```python
for x in range(-10, 10):
    for y in range(-10, 10):
        glVertex3f(x * 0.1, y * 0.1, 0)  # Tworzymy płaską siatkę
```
3. Odbicia w wodzie

3.1 Ogólna koncepcja

Odbicie sceny na powierzchni wody można uzyskać dwoma głównymi technikami:

Planar Reflection – renderujemy scenę odwróconą wokół płaszczyzny wody.

Environment Mapping – użycie cubemap lub spheremap do symulacji odbić.

3.2 Planar Reflection (odbicia płaskie)

Stencil Buffer / Clipping:

Zaznaczamy obszar wody w buforze szablonowym.

Rysowanie odbicia:

Odbijamy scenę: przed rysowaniem wszystkich obiektów negujemy wartość Y i przesuwamy o wysokość wody.

glScalef(1, -1, 1) + przesunięcie.

Mieszanie:

Włącz GL_BLEND i użyj odpowiednich alpha, aby uzyskać połysk i przezroczystość.
```
// Przykład uproszczony:
glEnable(GL_STENCIL_TEST);
glStencilFunc(GL_ALWAYS, 1, 0xFF);
glStencilOp(GL_KEEP, GL_KEEP, GL_REPLACE);
drawWaterPlane();            // rysujemy płaszczyznę wody, wpisując stencil=1

glStencilFunc(GL_EQUAL, 1, 0xFF);
glStencilOp(GL_KEEP, GL_KEEP, GL_KEEP);
glPushMatrix();
  glTranslatef(0, waterHeight*2, 0);
  glScalef(1, -1, 1);         // odbicie
  drawSceneObjects();         // rysujemy odbite obiekty
glPopMatrix();

// Następnie ponownie rysujemy wodę z blendingiem
drawWaterPlaneWithBlend();
glDisable(GL_STENCIL_TEST);
```
3.3 Environment Mapping (cubemap reflection)

Cubemap – załaduj tekstury 6-kierunkowe.

Shader:

W vertex shader oblicz wektor odbicia: `vec3 R = reflect(-viewDir, normal);`

W fragment shader użyj `textureCube(environmentMap, R) jako kolor odbicia.`

// Fragment shader:
```
uniform samplerCube envMap;
in vec3 reflectedDir;
out vec4 fragColor;

void main() {
    vec4 envColor = texture(envMap, normalize(reflectedDir));
    fragColor = mix(baseColor, envColor, reflectivity);
}
```
3.4 Wybór techniki

Planar Reflection – wierne odbicia, ale wymagające dodatkowego renderowania i zarządzania stencil.

Environment Mapping – szybsze, daje zbliżony efekt, ale odbija tylko otoczenie, nie uwzględnia innych dynamicznych obiektów.


