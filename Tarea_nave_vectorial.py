import pygame
import sys
import math
import random

# 1. Inicializar pygame
pygame.init()

# Tamaño de la ventana
ANCHO, ALTO = 800, 600

# Ventana con Double Buffering (DOUBLEBUF) para renderizado fluido
pantalla = pygame.display.set_mode((ANCHO, ALTO), pygame.DOUBLEBUF)
pygame.display.set_caption("Graficación 2D - Nave Espacial")
reloj = pygame.time.Clock()
FPS = 60

# ---------------------------------------------------------------
# Constantes del juego
# ---------------------------------------------------------------
VEL_ROTACION = 4          # grados por frame
VEL_NAVE = 4              # píxeles por frame
VEL_PROYECTIL = 10        # más rápido que la nave
VIDA_PROYECTIL = 90       # frames de vida (1.5 s a 60 FPS)
COOLDOWN_DISPARO = 250    # milisegundos entre disparos
MARGEN = 25               # margen para el screen wrapping

# ---------------------------------------------------------------
# 2. Transformación geométrica 2D (escala -> rotación -> traslación)
# ---------------------------------------------------------------
def transformar_vertice(vertice, pos_x, pos_y, escala, angulo):
    x, y = vertice
    # Escalamiento
    x_esc, y_esc = x * escala, y * escala
    # Rotación
    rad = math.radians(angulo)
    x_rot = x_esc * math.cos(rad) - y_esc * math.sin(rad)
    y_rot = x_esc * math.sin(rad) + y_esc * math.cos(rad)
    # Traslación al sistema de coordenadas de la pantalla
    return (x_rot + pos_x, y_rot + pos_y)


# Modelo local de la nave (coordenadas relativas al origen (0, 0)).
# La proa está en (0, -25). Los vértices están balanceados para que
# el centroide del triángulo quede exactamente en (0, 0) y así la
# nave gire sobre su propio centro.
modelo_nave = [(0, -25), (-15, 12.5), (15, 12.5)]

# Modelo de la llama del propulsor (se dibuja solo al avanzar)
modelo_llama = [(-6, 14), (0, 28), (6, 14)]

# ---------------------------------------------------------------
# Cielo estrellado
# ---------------------------------------------------------------
estrellas = []
for _ in range(160):
    estrellas.append({
        "x": random.randint(0, ANCHO),
        "y": random.randint(0, ALTO),
        "radio": random.choice([1, 1, 1, 2]),
        "brillo": random.randint(120, 255),
        "fase": random.uniform(0, math.tau),    # desfase del parpadeo
        "veloc": random.uniform(0.02, 0.08),    # velocidad del parpadeo
    })


def dibujar_estrellas(superficie, tiempo):
    for e in estrellas:
        # Parpadeo suave con seno
        factor = 0.65 + 0.35 * math.sin(tiempo * e["veloc"] * 60 + e["fase"])
        b = int(e["brillo"] * factor)
        pygame.draw.circle(superficie, (b, b, min(255, b + 20)),
                           (e["x"], e["y"]), e["radio"])


# ---------------------------------------------------------------
# Estado de la nave y de los proyectiles
# ---------------------------------------------------------------
pos_x, pos_y = 400, 300   # posición inicial
angulo = 0                # 0° = proa hacia arriba
escala = 1.0

# Lista dinámica de proyectiles: cada uno es un diccionario
# {"x", "y", "vx", "vy", "vida"}
proyectiles = []
ultimo_disparo = -COOLDOWN_DISPARO  # permite disparar desde el inicio

fuente = pygame.font.SysFont("consolas", 16)

# ---------------------------------------------------------------
# 3. Bucle principal
# ---------------------------------------------------------------
ejecutando = True
frame = 0
while ejecutando:
    frame += 1
    ahora = pygame.time.get_ticks()

    for evento in pygame.event.get():
        if evento.type == pygame.QUIT:
            ejecutando = False
        elif evento.type == pygame.KEYDOWN and evento.key == pygame.K_ESCAPE:
            ejecutando = False

    # --- Controles por teclado ---
    teclas = pygame.key.get_pressed()
    avanzando = False

    # Rotación (A / D o flechas izquierda / derecha)
    if teclas[pygame.K_a] or teclas[pygame.K_LEFT]:
        angulo -= VEL_ROTACION
    if teclas[pygame.K_d] or teclas[pygame.K_RIGHT]:
        angulo += VEL_ROTACION

    # Orientación de la proa. Con la matriz de rotación usada, el vector
    # que apunta a la proa (0, -1) rotado theta grados es (sin θ, -cos θ).
    theta = math.radians(angulo)
    dir_x = math.sin(theta)
    dir_y = -math.cos(theta)

    # Avance vectorial continuo (W o flecha arriba)
    if teclas[pygame.K_w] or teclas[pygame.K_UP]:
        pos_x += dir_x * VEL_NAVE
        pos_y += dir_y * VEL_NAVE
        avanzando = True

    # Screen wrapping: derecha -> izquierda, abajo -> arriba
    # (y también los casos inversos para que sea consistente)
    if pos_x > ANCHO + MARGEN:
        pos_x = -MARGEN
    elif pos_x < -MARGEN:
        pos_x = ANCHO + MARGEN
    if pos_y > ALTO + MARGEN:
        pos_y = -MARGEN
    elif pos_y < -MARGEN:
        pos_y = ALTO + MARGEN

    # Vértices de la nave en pantalla
    vertices_nave = [
        transformar_vertice(v, pos_x, pos_y, escala, angulo)
        for v in modelo_nave
    ]

    # Disparo (Barra espaciadora) con cooldown de 250 ms
    if teclas[pygame.K_SPACE] and ahora - ultimo_disparo >= COOLDOWN_DISPARO:
        ultimo_disparo = ahora
        # Posición exacta de la punta: primer vértice transformado
        punta_x, punta_y = vertices_nave[0]
        proyectiles.append({
            "x": punta_x,
            "y": punta_y,
            "vx": dir_x * VEL_PROYECTIL,
            "vy": dir_y * VEL_PROYECTIL,
            "vida": VIDA_PROYECTIL,
        })

    # --- Actualizar proyectiles y gestionar su ciclo de vida ---
    for p in proyectiles:
        p["x"] += p["vx"]
        p["y"] += p["vy"]
        p["vida"] -= 1

    # Eliminar los que salieron de la pantalla o agotaron su vida
    proyectiles = [
        p for p in proyectiles
        if p["vida"] > 0 and 0 <= p["x"] <= ANCHO and 0 <= p["y"] <= ALTO
    ]

    # ---------------- Renderizado ----------------
    pantalla.fill((10, 10, 22))               # fondo oscuro
    dibujar_estrellas(pantalla, frame / 60)   # cielo estrellado

    # Llama del propulsor
    if avanzando:
        llama = [
            transformar_vertice(v, pos_x, pos_y, escala, angulo)
            for v in modelo_llama
        ]
        pygame.draw.polygon(pantalla, (255, 140, 30), llama)

    # Nave
    pygame.draw.polygon(pantalla, (50, 255, 150), vertices_nave)
    pygame.draw.polygon(pantalla, (200, 255, 230), vertices_nave, 2)

    # Proyectiles
    for p in proyectiles:
        pygame.draw.circle(pantalla, (255, 240, 90),
                           (int(p["x"]), int(p["y"])), 3)

    # HUD
    texto = fuente.render(
        f"Proyectiles: {len(proyectiles)}   |   A/D: girar   W: avanzar   ESPACIO: disparar",
        True, (180, 180, 200))
    pantalla.blit(texto, (10, 10))

    pygame.display.flip()   # intercambia buffers (Double Buffering)
    reloj.tick(FPS)         # 60 FPS constantes

pygame.quit()
sys.exit()