#https://github.com/ranshaked123/123
import pygame
import threading
import time
import random
import psutil
import ollama


class Ball:
    def __init__(self, screen_width, screen_height):
        self.radius = 20
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
        self.x = random.randint(self.radius, self.screen_width - self.radius)
        self.y = random.randint(self.radius, self.screen_height - self.radius)
        self.jumps_amount = random.randint(3, 12)
        self.thread = None

    def update(self):
        """
        updates the balls position
        :return: NONE
        """
        thread_id = threading.current_thread().ident
        print(f"started: Ball thread ID: {thread_id} | Jumps: {self.jumps_amount}")

        while self.jumps_amount > 0:
            self.x = random.randint(self.radius, self.screen_width - self.radius)
            self.y = random.randint(self.radius, self.screen_height - self.radius)
            self.jumps_amount -= 1
            time.sleep(0.5)

        print(f"finished: Ball thread ID: {thread_id}")

    def draw(self, screen):
        """
        draws the ball on the screen
        :param screen: the screen
        :return: NONE
        """
        pygame.draw.circle(screen, self.color, (self.x, self.y), self.radius)


amount_of_balls_req = input("how many balls? ")
while not amount_of_balls_req.isdigit():
    print("please enter a valid non-negative number!")
    amount_of_balls_req = input("how many balls? ")

amount_of_balls_req = int(amount_of_balls_req)

pygame.init()
screen = pygame.display.set_mode((800, 600))
pygame.display.set_caption("screen")
clock = pygame.time.Clock()

running = True
balls = []

for i in range(amount_of_balls_req):
    new_ball = Ball(800, 600)
    new_ball.thread = threading.Thread(target=new_ball.update, daemon=True)
    balls.append(new_ball)
    new_ball.thread.start()

last_count = -1

while running and len(balls) > 0:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    for ball in balls[:]:
        if not ball.thread.is_alive():
            balls.remove(ball)

    if len(balls) != last_count:
        print(f"Active balls: {len(balls)}")
        last_count = len(balls)

    screen.fill((0, 0, 0))

    for ball in balls:
        ball.draw(screen)

    pygame.display.flip()
    clock.tick(60)

print("finished")
pygame.quit()
