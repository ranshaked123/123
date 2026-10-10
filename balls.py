
import pygame
import threading
import time
import random

class Ball:
    def __init__(self, screen_width, screen_height):
        self.radius = 20
        self.screen_width = screen_width
        self.screen_height = screen_height
        # random color
        self.color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
        # random place
        self.x = random.randint(self.radius,self.screen_width - self.radius)
        self.y = random.randint(self.radius,self.screen_height - self.radius)
        #random jumps amount
        self.jumps_amount = random.randint(1, 6)

    def update(self):
        while self.jumps_amount > 0:
            self.x = random.randint(self.radius, self.screen_width - self.radius)
            self.y = random.randint(self.radius, self.screen_height - self.radius)
            self.jumps_amount -= 1
            time.sleep(0.5)


    def draw(self, screen):
        pygame.draw.circle(screen, self.color,(self.x, self.y), self.radius)

while True:
    amount_of_balls_req = input("how many balls? ")
    if amount_of_balls_req.isdigit():
        break
    else:
        print("please enter a number!")

amount_of_balls_req = int(amount_of_balls_req)

pygame.init()
screen = pygame.display.set_mode((800, 600))
pygame.display.set_caption("screen")
clock = pygame.time.Clock()

running = True


balls = []
for i in range(amount_of_balls_req):
    new_ball = Ball(800, 600)
    balls.append(new_ball)

    ball_thread = threading.Thread(target=new_ball.update, daemon=True).start()



while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    for ball in balls:
        if ball.jumps_amount == 0:
            balls.remove(ball)

    screen.fill((0, 0, 0))

    for ball in balls:
        ball.draw(screen)
    print("amount of balls: " + str(len(balls)))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()