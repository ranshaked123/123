import multiprocessing
import random
import time
import pygame
import psutil
import ollama

WIDTH, HEIGHT = 800, 600
RADIUS = 20


def printProcess(printQueue):
    while True:
        msg = printQueue.get()
        if msg is None:
            break
        print(msg)


def ballProcess(ballID, size, updateQueue, printQueue):
    width, height = size
    color = tuple(random.randint(0, 255) for _ in range(3))
    x = random.randint(RADIUS, width - RADIUS)
    y = random.randint(RADIUS, height - RADIUS)

    printQueue.put(f"Ball {ballID} started")
    updateQueue.put(("update", ballID, x, y, color, RADIUS))

    for _ in range(random.randint(1, 20)):
        time.sleep(0.5)
        x = random.randint(RADIUS, width - RADIUS)
        y = random.randint(RADIUS, height - RADIUS)
        updateQueue.put(("update", ballID, x, y, color, RADIUS))

    updateQueue.put(("finished", ballID, x, y, color, RADIUS))
    printQueue.put(f"Ball {ballID} finished")


def collisionDetector(updateQueue, displayQueue, printQueue, totalBalls):
    balls = {}
    finished = set()
    printQueue.put("Collision Detector started")

    while len(finished) < totalBalls:
        kind, ballID, x, y, color, radius = updateQueue.get()

        balls[ballID] = {
            "x": x,
            "y": y,
            "color": color,
            "radius": radius,
            "finished": kind == "finished"
        }

        if kind == "finished":
            finished.add(ballID)

        active = [b for b in balls.values() if not b["finished"]]

        for i, first in enumerate(active):
            for second in active[i + 1:]:
                dx = second["x"] - first["x"]
                dy = second["y"] - first["y"]
                minDist = first["radius"] + second["radius"]
                distSq = dx * dx + dy * dy

                if distSq < minDist ** 2:
                    if distSq == 0:
                        dx, dy, distSq = 1, 0, 1

                    dist = distSq ** 0.5
                    overlap = minDist - dist
                    px = round(dx / dist * (overlap / 2 + 1))
                    py = round(dy / dist * (overlap / 2 + 1))

                    first["x"] -= px
                    first["y"] -= py
                    second["x"] += px
                    second["y"] += py

                    for ball in (first, second):
                        ball["x"] = max(RADIUS, min(WIDTH - RADIUS, ball["x"]))
                        ball["y"] = max(RADIUS, min(HEIGHT - RADIUS, ball["y"]))

        displayQueue.put({
            bid: (b["x"], b["y"], b["color"], b["radius"])
            for bid, b in balls.items() if not b["finished"]
        })

    displayQueue.put(None)
    printQueue.put("Collision Detector finished")


def cpuMonitor(cpuUsage, stopEvent, printQueue):
    printQueue.put("CPU Monitor started")

    while not stopEvent.is_set():
        cpuUsage.value = psutil.cpu_percent(interval=1)
        printQueue.put(f"CPU Usage: {cpuUsage.value:.1f}%")


def ollamaAgent(cpuUsage, stopEvent, printQueue):
    while not stopEvent.wait(5):
        try:
            usage = cpuUsage.value
            response = ollama.chat(model="gemma2",messages=[{"role": "system","content": "Analyze CPU usage. Classify it as normal, high, or critical. Be brief."},{"role": "user","content": f"Current CPU usage: {usage:.1f}%"}])
            printQueue.put(f"[AI AGENT] {response['message']['content']}")
        except Exception as e:
            printQueue.put(f"Ollama error: {e}")


def main():
    try:
        circleNum = int(input("Enter number of circles: "))
        if circleNum < 1:
            print("Enter a number greater than zero")
            return
    except ValueError:
        print("Enter a valid number")
        return

    updateQueue = multiprocessing.Queue()
    displayQueue = multiprocessing.Queue()
    printQueue = multiprocessing.Queue()

    cpuUsage = multiprocessing.Value('d', 0.0)
    stopEvent = multiprocessing.Event()

    printer = multiprocessing.Process(target=printProcess, args=(printQueue,))
    detector = multiprocessing.Process(target=collisionDetector,args=(updateQueue, displayQueue, printQueue, circleNum))
    monitor = multiprocessing.Process(target=cpuMonitor,args=(cpuUsage, stopEvent, printQueue))
    agent = multiprocessing.Process(target=ollamaAgent,args=(cpuUsage, stopEvent, printQueue))

    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Jumping Circles + Ollama AI")
    clock = pygame.time.Clock()

    printer.start()
    detector.start()
    monitor.start()
    agent.start()

    balls = []
    for ballID in range(circleNum):
        p = multiprocessing.Process(
            target=ballProcess,
            args=(ballID, (WIDTH, HEIGHT), updateQueue, printQueue)
        )
        p.start()
        balls.append(p)

    circles = {}
    running = True
    detectorFinished = False

    try:
        while running and not detectorFinished:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            while not displayQueue.empty():
                snapshot = displayQueue.get()
                if snapshot is None:
                    detectorFinished = True
                    break
                circles = snapshot

            screen.fill("black")
            for x, y, color, radius in circles.values():
                pygame.draw.circle(screen, color, (x, y), radius)

            pygame.display.flip()
            clock.tick(60)

    finally:
        for p in balls:
            p.join(timeout=2)
            if p.is_alive():
                p.terminate()
                p.join()

        if detector.is_alive():
            updateQueue.put(("finished", -1, 0, 0, (0, 0, 0), RADIUS))
            detector.join(timeout=2)
            if detector.is_alive():
                detector.terminate()
                detector.join()

        stopEvent.set()

        monitor.join(timeout=3)
        agent.join(timeout=10)

        for p in (monitor, agent):
            if p.is_alive():
                p.terminate()
                p.join()

        printQueue.put(None)
        printer.join(timeout=2)

        if printer.is_alive():
            printer.terminate()
            printer.join()

        updateQueue.close()
        displayQueue.close()
        printQueue.close()
        pygame.quit()

if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()